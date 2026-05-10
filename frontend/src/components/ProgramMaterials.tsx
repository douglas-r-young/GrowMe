import { useState } from "react";
import {
  BookOpen,
  Download,
  Loader2,
  Mail,
  PlayCircle,
  QrCode,
  Send,
  Users
} from "lucide-react";

import { api, waitForJob } from "../api";
import { AssetLibrary } from "./AssetLibrary";
import { JobProgress, MarkdownLite, PanelTitle, QrBlock } from "./shared";
import type { JobStatus, StateSnapshot } from "../types";

export function ProgramMaterials({
  sessionId,
  snapshot,
  onBack,
  onReload,
  onSnapshot
}: {
  sessionId: string;
  snapshot: StateSnapshot;
  onBack: () => void;
  onReload: () => Promise<void>;
  onSnapshot: (snapshot: StateSnapshot) => void;
}) {
  const [job, setJob] = useState<JobStatus | null>(null);
  const [busy, setBusy] = useState(false);
  const [sendStatus, setSendStatus] = useState("");

  async function build() {
    setBusy(true);
    const created = await api.createBuildJob(sessionId);
    const finalJob = await waitForJob(created.job_id, setJob);
    if (finalJob.status === "complete") await onReload();
    setBusy(false);
  }

  if (!snapshot.deck) {
    return (
      <section className="panel approval-card">
        <PanelTitle icon={<Download size={18} />} title="Build session package" />
        <p>Generate the session plan, assessment, deck, facilitator guide, and manager prompts from the approved design.</p>
        <JobProgress job={job} />
        <div className="footer-actions">
          <button className="button subtle" onClick={onBack}>Back</button>
          <button className="button primary" onClick={build} disabled={busy}>
            {busy ? <Loader2 className="spin" size={17} /> : <PlayCircle size={17} />}
            Build Program
          </button>
        </div>
      </section>
    );
  }

  const roster = Object.values(snapshot.commitments);
  return (
    <>
      <AssetLibrary sessionId={sessionId} assets={snapshot.assets} />
      <section className="panel qr-panel">
        <PanelTitle icon={<QrCode size={18} />} title="Program ready" />
        <div className="qr-grid">
          <QrBlock label="Pre-survey" url={snapshot.deck.pre_qr_url} src={`/api/sessions/${sessionId}/qr/pre`} />
          <QrBlock label="Commitment pick" url={snapshot.deck.post_qr_url} src={`/api/sessions/${sessionId}/qr/post`} />
        </div>
      </section>
      <section className="panel">
        <PanelTitle icon={<Users size={18} />} title="Learner roster" />
        {roster.length === 0 ? (
          <div className="empty-state">No commitments yet.</div>
        ) : (
          <div className="roster-list">
            {roster.map((entry) => (
              <div className="roster-row" key={String(entry.email)}>
                <strong>{String(entry.name)}</strong>
                <span>{String(entry.email)}</span>
                <span>{String(entry.behavior_name)}</span>
                <span>
                  {snapshot.checkins[String(entry.email).toLowerCase()]?.filter(([, done]) => done).length ?? 0} yes
                </span>
              </div>
            ))}
          </div>
        )}
      </section>
      <section className="panel">
        <PanelTitle icon={<Mail size={18} />} title="Send weekly nudges" />
        <div className="nudge-actions">
          {["1", "2", "3", "final"].map((week) => (
            <button
              className="button subtle"
              disabled={!roster.length || busy}
              key={week}
              onClick={async () => {
                const result = await api.sendWeek(sessionId, week);
                setSendStatus(result.errors[0] ?? `Sent ${result.sent} email(s).`);
              }}
            >
              <Send size={16} />
              {week === "final" ? "Final survey" : `Week ${week}`}
            </button>
          ))}
        </div>
        {sendStatus ? <p className="status-message">{sendStatus}</p> : null}
      </section>
      <section className="panel">
        <PanelTitle icon={<BookOpen size={18} />} title="Deck preview" />
        <div className="slide-preview-list">
          {snapshot.deck.slides.map((slide, index) => (
            <article className="slide-preview" key={`${slide.title}-${index}`}>
              <span>Slide {index + 1} · {slide.layout}</span>
              <h3>{slide.title}</h3>
              <MarkdownLite text={slide.body_md || String(slide.blocks.prompt ?? slide.blocks.promise ?? "")} />
            </article>
          ))}
        </div>
      </section>
    </>
  );
}
