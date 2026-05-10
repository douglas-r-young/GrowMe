import { useState } from "react";
import { ClipboardCheck, Download, Loader2, PenLine, PlayCircle, RefreshCcw, Target } from "lucide-react";

import { api, waitForJob } from "../api";
import { JobProgress, MarkdownLite, PanelTitle } from "./shared";
import type { JobStatus, StateSnapshot } from "../types";

export function DesignApproval({
  sessionId,
  snapshot,
  onBack,
  onSnapshot,
  onContinue
}: {
  sessionId: string;
  snapshot: StateSnapshot;
  onBack: () => void;
  onSnapshot: (snapshot: StateSnapshot) => void;
  onContinue: () => void;
}) {
  const [markdown, setMarkdown] = useState(
    snapshot.design_doc_edited_md ?? snapshot.design_doc?.full_markdown ?? ""
  );
  const [job, setJob] = useState<JobStatus | null>(null);
  const [busy, setBusy] = useState(false);

  async function runDesign() {
    setBusy(true);
    const created = await api.createDesignJob(sessionId);
    const finalJob = await waitForJob(created.job_id, setJob);
    if (finalJob.status === "complete") {
      const next = await api.session(sessionId);
      setMarkdown(next.design_doc_edited_md ?? "");
      onSnapshot(next);
    }
    setBusy(false);
  }

  if (!snapshot.design_doc) {
    return (
      <section className="panel approval-card">
        <PanelTitle icon={<ClipboardCheck size={18} />} title="Generate design document" />
        <p>Runs company research, behavior research, and the pedagogy-aligned design writer.</p>
        <JobProgress job={job} />
        <div className="footer-actions">
          <button className="button subtle" onClick={onBack}>Back</button>
          <button className="button primary" onClick={runDesign} disabled={busy}>
            {busy ? <Loader2 className="spin" size={17} /> : <PlayCircle size={17} />}
            Generate Design Document
          </button>
        </div>
      </section>
    );
  }

  return (
    <>
      <section className="panel approval-card">
        <p className="eyebrow">Research-backed design</p>
        <h2>{snapshot.deck?.title ?? "Program design ready for approval"}</h2>
        <p>{snapshot.design_doc.integration_learning_objective}</p>
        <div className="meta-strip">
          <span>Behaviors: {snapshot.design_doc.behavior_objectives.length}</span>
          <span>Audience: {String(snapshot.setup.audience_preset ?? "Not set")}</span>
          <span>Transfer plan: Ready</span>
        </div>
      </section>
      <section className="panel">
        <PanelTitle icon={<Target size={18} />} title="Target Behaviors" />
        <div className="objective-list">
          {snapshot.design_doc.behavior_objectives.map((objective) => (
            <div className="objective-row" key={objective}>{objective}</div>
          ))}
        </div>
      </section>
      <section className="panel">
        <PanelTitle icon={<RefreshCcw size={18} />} title="Transfer Plan" />
        <MarkdownLite text={snapshot.design_doc.transfer_plan_md} />
      </section>
      <section className="panel">
        <PanelTitle icon={<PenLine size={18} />} title="Editable Design Markdown" />
        <textarea value={markdown} onChange={(event) => setMarkdown(event.target.value)} rows={12} />
      </section>
      <div className="footer-actions">
        <button className="button subtle" onClick={onBack}>Back</button>
        <button
          className="button subtle"
          onClick={async () => {
            const next = await api.saveDesignDoc(sessionId, markdown);
            onSnapshot(next);
          }}
        >
          Save edits
        </button>
        <button className="button primary" onClick={onContinue}>
          <Download size={17} />
          Continue to Program Materials
        </button>
      </div>
    </>
  );
}
