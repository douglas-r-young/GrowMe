"""Request/response models for the GrowMe API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SetupRequest(BaseModel):
    program_name: str = ""
    company_url: str
    company_alias: str
    audience_preset: str
    audience_cohort: str
    audience_program_fmt: str
    audience_notes: str = ""
    reference_urls: list[str] = Field(default_factory=list)
    uploaded_file_names: list[str] = Field(default_factory=list)


class BehaviorsRequest(BaseModel):
    selected_behavior_ids: list[str] = Field(min_length=3, max_length=3)


class DesignDocUpdateRequest(BaseModel):
    markdown: str = Field(min_length=1)


class LikertSubmission(BaseModel):
    learner_name: str = Field(min_length=1)
    learner_id: str = Field(min_length=1)
    frequency_answers: dict[str, str]


class PostCommitmentSubmission(BaseModel):
    learner_name: str = Field(min_length=1)
    learner_email: str = Field(min_length=1)
    behavior_id: str = Field(min_length=1)


class CheckinSubmission(BaseModel):
    learner: str = Field(min_length=1)
    week: int = Field(ge=1, le=3)
    done: bool


class SendWeekRequest(BaseModel):
    week: Literal["1", "2", "3", "final"]


class JobCreateResponse(BaseModel):
    job_id: str


class JobResponse(BaseModel):
    job_id: str
    kind: str
    session_id: str
    status: Literal["queued", "running", "complete", "error"]
    messages: list[str]
    error: str | None = None


class AssetRow(BaseModel):
    id: str
    name: str
    type: str
    status: str
    description: str
    download_url: str | None = None
