import { Loader2 } from "lucide-react";
import type { JobStatus, LastJobSnapshot } from "../types";

export function StepHeader({ step }: { step: number }) {
  const labels = ["Program Setup", "Training Objectives", "Design Approval", "Program Materials"];
  const progress = [25, 50, 75, 100][step];
  return (
    <header className="page-header">
      <div className="progress-line">
        <span>Step {step + 1} of 4</span>
        <div className="progress-track">
          <div style={{ width: `${progress}%` }} />
        </div>
        <span>{progress}% complete</span>
      </div>
      <h1>{labels[step]}</h1>
      <p>Build behavior-change training materials from the current GrowMe backend outputs.</p>
    </header>
  );
}

export function PanelTitle({ icon, title }: { icon: React.ReactNode; title: string }) {
  return (
    <div className="panel-title">
      {icon}
      <h2>{title}</h2>
    </div>
  );
}

export function JobProgress({ job }: { job: JobStatus | null }) {
  if (!job) return null;
  return (
    <div className="job-progress">
      <strong>{job.status === "error" ? "Job failed" : "Working..."}</strong>
      {job.messages.map((message) => <span key={message}>{message}</span>)}
      {job.error ? <span className="error-text">{job.error}</span> : null}
    </div>
  );
}

export function StaleJobNotice({ lastJob }: { lastJob: LastJobSnapshot | null }) {
  if (!lastJob) return null;
  if (lastJob.status === "complete" || lastJob.status === "queued") return null;
  if (lastJob.status === "running") {
    return (
      <div className="job-progress">
        <strong>Earlier job did not finish</strong>
        <span>The previous {lastJob.kind} job was running when the server restarted. Re-run to continue.</span>
        {lastJob.messages.slice(-3).map((message) => <span key={message}>{message}</span>)}
      </div>
    );
  }
  return (
    <div className="job-progress">
      <strong>Previous {lastJob.kind} job failed</strong>
      {lastJob.error ? <span className="error-text">{lastJob.error}</span> : null}
      {lastJob.messages.slice(-3).map((message) => <span key={message}>{message}</span>)}
    </div>
  );
}

export function QrBlock({ label, url, src }: { label: string; url: string; src: string }) {
  return (
    <div className="qr-block">
      <img src={src} alt={`${label} QR code`} />
      <strong>{label}</strong>
      <code>{url}</code>
    </div>
  );
}

export function MarkdownLite({ text }: { text: string }) {
  return (
    <div className="markdown-lite">
      {text.split("\n").filter(Boolean).map((line) => (
        <p key={line}>{line.replace(/^#+\s*/, "")}</p>
      ))}
    </div>
  );
}

export function SimpleLearnerShell({ title, children }: { title: string; children?: React.ReactNode }) {
  return (
    <main className="learner-shell">
      <p className="brand">GrowMe</p>
      <section className="panel">
        <h1>{title}</h1>
        {children}
      </section>
    </main>
  );
}

export function LoadingScreen() {
  return (
    <main className="loading">
      <Loader2 className="spin" /> Loading GrowMe...
    </main>
  );
}

export function ErrorScreen({ message }: { message: string }) {
  return <main className="loading error-text">{message}</main>;
}

export function toggle(items: string[], id: string): string[] {
  return items.includes(id) ? items.filter((item) => item !== id) : [...items, id];
}
