import { useState } from "react";
import { CheckCircle2, GraduationCap } from "lucide-react";

import { PanelTitle, toggle } from "./shared";
import type { BehaviorMenuPayload, BehaviorTemplate, StateSnapshot } from "../types";

export function TrainingObjectives({
  menu,
  snapshot,
  onBack,
  onContinue
}: {
  menu: BehaviorMenuPayload;
  snapshot: StateSnapshot;
  onBack: () => void;
  onContinue: (ids: string[]) => Promise<void>;
}) {
  const defaults = snapshot.selected_behavior_ids.length
    ? snapshot.selected_behavior_ids
    : menu.default_selected_behavior_ids;
  const [selected, setSelected] = useState<string[]>(defaults);
  const [busy, setBusy] = useState(false);
  return (
    <section className="panel">
      <PanelTitle icon={<GraduationCap size={18} />} title="Sales behaviors" />
      <p className="section-copy">
        Pick exactly three observable behaviors. These selections drive research, design, assessment, and deck generation.
      </p>
      <div className="behavior-list">
        {menu.behaviors.map((behavior) => (
          <BehaviorOption
            behavior={behavior}
            selected={selected.includes(behavior.id)}
            key={behavior.id}
            onToggle={() => setSelected(toggle(selected, behavior.id))}
          />
        ))}
      </div>
      <div className="footer-actions">
        <button className="button subtle" type="button" onClick={onBack}>Back</button>
        <span className={selected.length === 3 ? "pill ok" : "pill"}>Selected {selected.length} / 3</span>
        <button
          className="button primary"
          type="button"
          disabled={selected.length !== 3 || busy}
          onClick={async () => {
            setBusy(true);
            await onContinue(selected);
            setBusy(false);
          }}
        >
          <CheckCircle2 size={17} />
          Continue to Design Approval
        </button>
      </div>
    </section>
  );
}

function BehaviorOption({
  behavior,
  selected,
  onToggle
}: {
  behavior: BehaviorTemplate;
  selected: boolean;
  onToggle: () => void;
}) {
  return (
    <label className={`behavior-option ${selected ? "selected" : ""}`}>
      <input type="checkbox" checked={selected} onChange={onToggle} />
      <span>
        <strong>{behavior.name}</strong>
        <small>{behavior.framework_origin}</small>
        <p>{behavior.description}</p>
      </span>
    </label>
  );
}
