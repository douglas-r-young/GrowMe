import { ArrowRight, BarChart3, FileText, Plus, Sparkles } from "lucide-react";

import type { BehaviorMenuPayload, StateSnapshot } from "../types";

type Props = {
  menu: BehaviorMenuPayload;
  snapshot: StateSnapshot;
  onAddProgram: () => void;
  onOpenProgram: () => void;
  onViewAnalytics: () => void;
};

export function HomeDashboard({
  menu,
  snapshot,
  onAddProgram,
  onOpenProgram,
  onViewAnalytics
}: Props) {
  const programName = String(snapshot.setup.program_name ?? snapshot.deck?.title ?? "Photon DB discovery sprint");
  const companyName = String(snapshot.setup.company_alias ?? "Photon DB");
  const selectedCount = snapshot.selected_behavior_ids.length;
  const status = snapshot.deck
    ? "Program ready"
    : snapshot.design_doc
      ? "Design ready"
      : selectedCount === 3
        ? "Objectives selected"
        : "Draft";
  const artifactLabel = snapshot.assets.length
    ? `${snapshot.assets.length} material${snapshot.assets.length === 1 ? "" : "s"} ready`
    : "No materials generated";
  const selectedNames = snapshot.selected_behavior_ids
    .map((id) => menu.behaviors.find((behavior) => behavior.id === id)?.name)
    .filter(Boolean);

  return (
    <div className="home-dashboard">
      <header className="home-hero">
        <div>
          <p className="eyebrow">Hackathon control room</p>
          <h1>Home</h1>
          <p>
            Keep the demo path tight: start a Photon DB program, return to generated materials,
            or jump into post-training analytics.
          </p>
        </div>
        <button className="button primary" type="button" onClick={onAddProgram}>
          <Plus size={17} />
          Add Program
        </button>
      </header>

      <section className="home-section">
        <div className="section-header">
          <div>
            <p className="eyebrow">Active work</p>
            <h2>Current Programs</h2>
          </div>
        </div>
        <article className="program-card">
          <div className="program-card-main">
            <span className="program-card-icon">
              <Sparkles size={20} />
            </span>
            <div>
              <p className="program-card-kicker">{companyName}</p>
              <h3>{programName}</h3>
              <p>
                {selectedCount || 0} of 3 behaviors selected. {artifactLabel}.
              </p>
            </div>
          </div>

          <div className="program-card-meta">
            <span className="pill ok">{status}</span>
          </div>

          <div className="program-card-behaviors">
            {(selectedNames.length ? selectedNames : ["Quantify", "Connect", "Differentiate"]).slice(0, 3).map((name) => (
              <span key={name}>{name}</span>
            ))}
          </div>

          <div className="program-card-actions">
            <button className="button subtle" type="button" onClick={onOpenProgram}>
              <FileText size={16} />
              Open program
            </button>
            <button className="button subtle" type="button" onClick={onViewAnalytics} disabled={!snapshot.deck}>
              <BarChart3 size={16} />
              View analytics
            </button>
            <button className="button primary" type="button" onClick={onOpenProgram}>
              Continue
              <ArrowRight size={16} />
            </button>
          </div>
        </article>
      </section>
    </div>
  );
}
