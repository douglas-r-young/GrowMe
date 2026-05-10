"""FastAPI app that exposes the existing GrowMe pipeline to React."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse, Response
from fastapi.encoders import jsonable_encoder

from growme.api import store
from growme.api.jobs import Job, jobs
from growme.api.models import (
    AssetRow,
    BehaviorsRequest,
    CheckinSubmission,
    DesignDocUpdateRequest,
    JobCreateResponse,
    JobResponse,
    LikertSubmission,
    PostCommitmentSubmission,
    SendWeekRequest,
    SetupRequest,
)
from growme.audience import compose_audience_description
from growme.behavior_menu import BEHAVIOR_MENU, default_pic_behavior_ids
from growme.commitment_templates import commitment_for
from growme.qr import generate_qr_png
from growme.schemas import AssessmentResponse, Commitment, ProgramAssessment, WizardInputs

app = FastAPI(title="GrowMe API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _public_url() -> str:
    return os.environ.get("GROWME_PUBLIC_URL", "http://localhost:5173").rstrip("/")


def _session_exists(session_id: str) -> bool:
    return store.path_for(session_id).exists()


def _require_session(session_id: str) -> dict[str, Any]:
    if not _session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    return store.load(session_id)


def _wizard_inputs_from_state(data: dict[str, Any]) -> WizardInputs:
    audience_description = data.get("audience_description") or compose_audience_description(
        target_audience=data.get("audience_preset", "Enterprise AEs"),
        cohort_size=data.get("audience_cohort", "10-20 participants"),
        program_format=data.get("audience_program_fmt", "Single session (demo)"),
        notes=data.get("audience_notes", ""),
    )
    return WizardInputs(
        company_url=data.get("company_url") or "neon.tech",
        company_alias=data.get("company_alias") or "Photon DB",
        audience_description=audience_description,
        selected_behavior_ids=data.get("selected_behavior_ids") or default_pic_behavior_ids(),
        reference_urls=list(data.get("reference_urls") or []),
    )


def _snapshot(session_id: str) -> dict[str, Any]:
    data = _require_session(session_id)
    setup = {
        key: data.get(key)
        for key in (
            "program_name",
            "company_url",
            "company_alias",
            "audience_preset",
            "audience_cohort",
            "audience_program_fmt",
            "audience_notes",
            "reference_urls",
            "uploaded_file_names",
        )
    }
    try:
        wizard_inputs = _wizard_inputs_from_state(data)
    except Exception:
        wizard_inputs = None
    return jsonable_encoder(
        {
            "session_uuid": session_id,
            "setup": setup,
            "wizard_inputs": wizard_inputs,
            "selected_behavior_ids": data.get("selected_behavior_ids") or [],
            "enriched_context": data.get("enriched_context"),
            "design_doc": data.get("design_doc"),
            "design_doc_edited_md": data.get("design_doc_edited_md"),
            "session_plan": data.get("session_plan"),
            "program_assessment": data.get("program_assessment"),
            "deck": data.get("deck"),
            "deck_audit_report": data.get("deck_audit_report"),
            "assessment_responses": data.get("assessment_responses", []),
            "commitments": data.get("commitments", {}),
            "checkins": data.get("checkins", {}),
            "nudges": data.get("nudges", []),
            "delta_report": data.get("delta_report"),
            "sim_complete": data.get("sim_complete", False),
            "last_job": data.get("last_job"),
            "assets": _asset_rows(session_id, data),
        }
    )


def _asset_rows(session_id: str, data: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[AssetRow] = []
    deck = data.get("deck")
    assessment = data.get("program_assessment")
    if deck and deck.pptx_path:
        rows.append(
            AssetRow(
                id="deck",
                name="Session Deck",
                type="Presentation",
                status="Ready",
                description="PowerPoint deck with QR survey slides",
                download_url=f"/api/sessions/{session_id}/downloads/deck",
            )
        )
    if deck and deck.facilitator_guide_md:
        rows.append(
            AssetRow(
                id="facilitator-guide",
                name="Facilitator Guide",
                type="Guide",
                status="Ready",
                description="Facilitator-facing session guide",
                download_url=f"/api/sessions/{session_id}/downloads/facilitator-guide",
            )
        )
    if deck and deck.manager_briefing_md:
        rows.append(
            AssetRow(
                id="manager-briefing",
                name="Manager 1:1 Briefing",
                type="Guide",
                status="Ready",
                description="Manager prompts for transfer of training",
                download_url=f"/api/sessions/{session_id}/downloads/manager-briefing",
            )
        )
    if assessment:
        rows.append(
            AssetRow(
                id="program-assessment",
                name="Program Assessment",
                type="Assessment",
                status="Ready",
                description="Pre/final frequency questions and commitments",
                download_url=f"/api/sessions/{session_id}/downloads/program-assessment",
            )
        )
    if data.get("nudges"):
        rows.append(
            AssetRow(
                id="nudges",
                name="Generated Nudges",
                type="Nudge",
                status="Ready",
                description="Learner and manager follow-up messages",
                download_url=f"/api/sessions/{session_id}/downloads/nudges",
            )
        )
    if data.get("delta_report"):
        rows.append(
            AssetRow(
                id="delta-report",
                name="Delta Report",
                type="Report",
                status="Ready",
                description="Behavior movement and reinforcement summary",
                download_url=f"/api/sessions/{session_id}/downloads/delta-report",
            )
        )
    return jsonable_encoder(rows)


def _job_response(job: Job) -> JobResponse:
    return JobResponse(
        job_id=job.id,
        kind=job.kind,
        session_id=job.session_id,
        status=job.status,
        messages=job.messages,
        error=job.error,
    )


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/sessions")
def create_session() -> dict[str, str]:
    return {"session_uuid": store.new_session_id()}


@app.get("/api/behavior-menu")
def behavior_menu() -> dict[str, Any]:
    return jsonable_encoder(
        {
            "behaviors": list(BEHAVIOR_MENU.values()),
            "default_selected_behavior_ids": default_pic_behavior_ids(),
        }
    )


@app.get("/api/sessions/{session_id}")
def get_session(session_id: str) -> dict[str, Any]:
    return _snapshot(session_id)


@app.put("/api/sessions/{session_id}/setup")
def save_setup(session_id: str, payload: SetupRequest) -> dict[str, Any]:
    _require_session(session_id)
    audience_description = compose_audience_description(
        target_audience=payload.audience_preset,
        cohort_size=payload.audience_cohort,
        program_format=payload.audience_program_fmt,
        notes=payload.audience_notes,
    )
    store.update_many(
        session_id,
        {
            **payload.model_dump(),
            "audience_description": audience_description,
        },
    )
    return _snapshot(session_id)


@app.put("/api/sessions/{session_id}/behaviors")
def save_behaviors(session_id: str, payload: BehaviorsRequest) -> dict[str, Any]:
    _require_session(session_id)
    missing = [bid for bid in payload.selected_behavior_ids if bid not in BEHAVIOR_MENU]
    if missing:
        raise HTTPException(status_code=422, detail=f"Unknown behavior IDs: {missing}")
    store.update(session_id, "selected_behavior_ids", payload.selected_behavior_ids)
    return _snapshot(session_id)


@app.post("/api/sessions/{session_id}/design-jobs", response_model=JobCreateResponse)
def create_design_job(session_id: str) -> JobCreateResponse:
    _require_session(session_id)
    job = jobs.create(kind="design", session_id=session_id, target=lambda j: _run_design_job(session_id, j))
    return JobCreateResponse(job_id=job.id)


@app.put("/api/sessions/{session_id}/design-doc")
def save_design_doc(session_id: str, payload: DesignDocUpdateRequest) -> dict[str, Any]:
    _require_session(session_id)
    store.update(session_id, "design_doc_edited_md", payload.markdown)
    return _snapshot(session_id)


@app.post("/api/sessions/{session_id}/build-jobs", response_model=JobCreateResponse)
def create_build_job(session_id: str) -> JobCreateResponse:
    _require_session(session_id)
    job = jobs.create(kind="build", session_id=session_id, target=lambda j: _run_build_job(session_id, j))
    return JobCreateResponse(job_id=job.id)


@app.get("/api/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: str) -> JobResponse:
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return _job_response(job)


@app.get("/api/sessions/{session_id}/assets")
def get_assets(session_id: str) -> dict[str, Any]:
    data = _require_session(session_id)
    return {"assets": _asset_rows(session_id, data)}


@app.get("/api/sessions/{session_id}/downloads/{asset_id}")
def download_asset(session_id: str, asset_id: str):
    data = _require_session(session_id)
    deck = data.get("deck")
    if asset_id == "deck":
        if not deck or not deck.pptx_path:
            raise HTTPException(status_code=404, detail="Deck not generated")
        return FileResponse(
            deck.pptx_path,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            filename="growme_deck.pptx",
        )
    if asset_id == "facilitator-guide":
        if not deck or not deck.facilitator_guide_md:
            raise HTTPException(status_code=404, detail="Guide not generated")
        return PlainTextResponse(
            deck.facilitator_guide_md,
            media_type="text/markdown",
            headers={"Content-Disposition": 'attachment; filename="facilitator_guide.md"'},
        )
    if asset_id == "manager-briefing":
        if not deck or not deck.manager_briefing_md:
            raise HTTPException(status_code=404, detail="Manager briefing not generated")
        return PlainTextResponse(
            deck.manager_briefing_md,
            media_type="text/markdown",
            headers={"Content-Disposition": 'attachment; filename="manager_1to1_prompts.md"'},
        )
    if asset_id == "program-assessment":
        assessment = data.get("program_assessment")
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not generated")
        return Response(
            json.dumps(jsonable_encoder(assessment), indent=2),
            media_type="application/json",
            headers={"Content-Disposition": 'attachment; filename="program_assessment.json"'},
        )
    if asset_id == "delta-report":
        report = data.get("delta_report")
        if not report:
            raise HTTPException(status_code=404, detail="Delta report not generated")
        return PlainTextResponse(
            report.full_markdown,
            media_type="text/markdown",
            headers={"Content-Disposition": 'attachment; filename="delta_report.md"'},
        )
    if asset_id == "nudges":
        nudges = data.get("nudges")
        if not nudges:
            raise HTTPException(status_code=404, detail="Nudges not generated")
        return Response(
            json.dumps(jsonable_encoder(nudges), indent=2),
            media_type="application/json",
            headers={"Content-Disposition": 'attachment; filename="nudges.json"'},
        )
    raise HTTPException(status_code=404, detail="Unknown asset")


@app.get("/api/sessions/{session_id}/qr/{kind}")
def qr_png(session_id: str, kind: Literal["pre", "post"]):
    _require_session(session_id)
    url = f"{_public_url()}/?assessment={session_id}&kind={kind}"
    return Response(generate_qr_png(url), media_type="image/png")


@app.get("/api/assessment/{session_id}/config")
def assessment_config(
    session_id: str,
    kind: Literal["pre", "post", "final", "checkin"] = Query("pre"),
) -> dict[str, Any]:
    data = _require_session(session_id)
    if kind in ("pre", "final"):
        assessment = data.get("program_assessment")
        if assessment is None:
            raise HTTPException(status_code=404, detail="Assessment not generated")
        return {"kind": kind, "assessment": jsonable_encoder(assessment)}
    if kind == "post":
        selected_ids = data.get("selected_behavior_ids") or []
        options = []
        for behavior_id in selected_ids[:3]:
            behavior = BEHAVIOR_MENU.get(behavior_id)
            if behavior is not None:
                options.append(
                    {
                        "behavior_id": behavior_id,
                        "behavior_name": behavior.name,
                        "commitment_text": commitment_for(behavior_id),
                    }
                )
        return {"kind": kind, "commitment_options": options}
    return {"kind": kind}


@app.post("/api/assessment/{session_id}/pre")
def submit_pre(session_id: str, payload: LikertSubmission) -> dict[str, str]:
    _append_likert_response(session_id, payload, "pre")
    return {"status": "recorded"}


@app.post("/api/assessment/{session_id}/final")
def submit_final(session_id: str, payload: LikertSubmission) -> dict[str, str]:
    _append_likert_response(session_id, payload, "post")
    return {"status": "recorded"}


@app.post("/api/assessment/{session_id}/post")
def submit_post(session_id: str, payload: PostCommitmentSubmission) -> dict[str, str]:
    data = _require_session(session_id)
    behavior = BEHAVIOR_MENU.get(payload.behavior_id)
    if behavior is None:
        raise HTTPException(status_code=422, detail="Unknown behavior ID")
    commitment_text = commitment_for(payload.behavior_id)
    commitment = Commitment.from_string(commitment_text)
    response = AssessmentResponse(
        session_uuid=session_id,
        learner_id=payload.learner_email.strip(),
        learner_name=payload.learner_name.strip(),
        kind="post",
        frequency_answers={},
        commitment=commitment,
    )
    responses = list(data.get("assessment_responses", []))
    responses.append(response)
    roster = dict(data.get("commitments", {}))
    roster[payload.learner_email.strip().lower()] = {
        "email": payload.learner_email.strip(),
        "name": payload.learner_name.strip(),
        "behavior_id": payload.behavior_id,
        "behavior_name": behavior.name,
        "commitment_text": commitment_text,
    }
    store.update_many(session_id, {"assessment_responses": responses, "commitments": roster})
    return {"status": "recorded"}


@app.post("/api/assessment/{session_id}/checkin")
def submit_checkin(session_id: str, payload: CheckinSubmission) -> dict[str, str]:
    data = _require_session(session_id)
    key = payload.learner.strip().lower()
    checkins = dict(data.get("checkins", {}))
    bucket = list(checkins.get(key, []))
    bucket.append((payload.week, payload.done))
    checkins[key] = bucket
    store.update(session_id, "checkins", checkins)
    return {"status": "recorded"}


@app.post("/api/sessions/{session_id}/nudges/send-week")
def send_weekly_nudges(session_id: str, payload: SendWeekRequest) -> dict[str, Any]:
    data = _require_session(session_id)
    roster = data.get("commitments", {}) or {}
    if not roster:
        raise HTTPException(status_code=409, detail="No learner commitments recorded")

    from growme.email.smtp_client import SMTPSendError, send_email
    from growme.email.weekly_nudge import build_email, build_final_email

    sent = 0
    errors: list[str] = []
    for entry in roster.values():
        try:
            if payload.week == "final":
                subject, html = build_final_email(
                    learner_email=entry["email"],
                    learner_name=entry.get("name", ""),
                    base_url=_public_url(),
                    session_uuid=session_id,
                )
            else:
                subject, html = build_email(
                    learner_email=entry["email"],
                    learner_name=entry.get("name", ""),
                    commitment_text=entry.get("commitment_text", ""),
                    week=int(payload.week),
                    base_url=_public_url(),
                    session_uuid=session_id,
                )
            send_email(entry["email"], subject, html)
            sent += 1
        except SMTPSendError as exc:
            errors.append(str(exc))
            break
        except Exception as exc:
            errors.append(f"{entry.get('email', '?')}: {exc}")
    return {"sent": sent, "errors": errors}


@app.post("/api/sessions/{session_id}/simulation")
def run_simulation(session_id: str) -> dict[str, Any]:
    data = _require_session(session_id)
    deck = data.get("deck")
    enriched = data.get("enriched_context")
    if deck is None or enriched is None:
        raise HTTPException(status_code=409, detail="Build a program before running simulation")

    from growme.assessment import fixtures as afix
    from growme.delta_report.node import run as run_delta
    from growme.nudges.node import generate_for_post_responses

    pre = afix.pre_responses(session_id, deck.behavior_ids)
    post = afix.post_responses(session_id, deck.behavior_ids)
    responses = pre + post
    nudges = generate_for_post_responses(post, enriched)
    report = run_delta(responses, enriched)
    store.update_many(
        session_id,
        {
            "assessment_responses": responses,
            "nudges": nudges,
            "delta_report": report,
            "sim_complete": True,
        },
    )
    return _snapshot(session_id)


def _append_likert_response(
    session_id: str,
    payload: LikertSubmission,
    kind: Literal["pre", "post"],
) -> None:
    data = _require_session(session_id)
    assessment: ProgramAssessment | None = data.get("program_assessment")
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not generated")
    expected = {q.behavior_id for q in assessment.pre_questions}
    if set(payload.frequency_answers) != expected:
        raise HTTPException(status_code=422, detail="Answer all assessment questions")
    response = AssessmentResponse(
        session_uuid=session_id,
        learner_id=payload.learner_id.strip(),
        learner_name=payload.learner_name.strip(),
        kind=kind,
        frequency_answers=payload.frequency_answers,
        commitment=None,
    )
    responses = list(data.get("assessment_responses", []))
    responses.append(response)
    store.update(session_id, "assessment_responses", responses)


def _run_design_job(session_id: str, job: Job) -> None:
    from growme.design_doc.node import run as run_design_doc
    from growme.research.node import run as run_research

    data = _require_session(session_id)
    inputs = _wizard_inputs_from_state(data)
    job.log("Phase A/B research...")
    enriched = run_research(inputs)
    job.log(f"Research complete: {len(enriched.sources_used)} sources.")
    job.log("Generating design document...")
    doc = run_design_doc(enriched, inputs)
    store.update_many(
        session_id,
        {
            "wizard_inputs": inputs,
            "enriched_context": enriched,
            "design_doc": doc,
            "design_doc_edited_md": doc.full_markdown,
        },
    )
    job.log("Design document ready.")


def _run_build_job(session_id: str, job: Job) -> None:
    from growme.assessment.generator import generate_program_assessment
    from growme.decks.builder import build_deck, collect_image_prompts
    from growme.decks.images import generate_deck_images
    from growme.decks.llm import gen_facilitator_guide, gen_manager_briefing, plan_deck_audited
    from growme.decks.pptx import export_pptx
    from growme.sessions.plan_node import run as run_plan

    data = _require_session(session_id)
    enriched = data.get("enriched_context")
    edited_md = data.get("design_doc_edited_md")
    if enriched is None or not edited_md:
        raise ValueError("Generate and approve a design document first")
    inputs = _wizard_inputs_from_state(data)
    session_dir = store.artifact_dir(session_id)

    job.log("Session plan...")
    plan = run_plan(edited_md, enriched, inputs)
    store.update(session_id, "session_plan", plan)

    job.log("Assessment...")
    try:
        assessment = generate_program_assessment(enriched, inputs)
    except Exception:
        from growme.assessment.generator import generate_program_assessment_offline

        assessment = generate_program_assessment_offline(inputs.selected_behavior_ids)
    store.update(session_id, "program_assessment", assessment)

    job.log("Planning deck and running audit...")
    deck_plan, audit_report = plan_deck_audited(plan, enriched)
    store.update(session_id, "deck_audit_report", audit_report if audit_report and audit_report.overall_grade != "pass" else None)

    prompts = collect_image_prompts(deck_plan)
    job.log(f"Generating {len(prompts)} deck images...")
    image_paths = generate_deck_images(prompts)

    job.log("Facilitator guide...")
    guide_md = gen_facilitator_guide(plan, enriched, deck_plan=deck_plan)

    job.log("Manager briefing...")
    try:
        manager_briefing_md = gen_manager_briefing(
            plan=plan,
            enriched=enriched,
            deck_plan=deck_plan,
            design_doc_md=edited_md,
        )
    except Exception:
        manager_briefing_md = ""

    job.log("Composing deck and exporting PowerPoint...")
    pre_qr_url = f"{_public_url()}/?assessment={session_id}&kind=pre"
    post_qr_url = f"{_public_url()}/?assessment={session_id}&kind=post"
    deck = build_deck(
        plan=plan,
        enriched=enriched,
        deck_plan=deck_plan,
        pre_qr_url=pre_qr_url,
        post_qr_url=post_qr_url,
        facilitator_guide_md=guide_md,
        manager_briefing_md=manager_briefing_md,
        image_paths=image_paths,
        company_alias=inputs.company_alias,
    )
    pptx_path = session_dir / "deck.pptx"
    export_pptx(deck, pptx_path)
    store.update(session_id, "deck", deck)
    job.log("Program materials ready.")
