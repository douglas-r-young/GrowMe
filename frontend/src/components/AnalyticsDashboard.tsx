import { useMemo, useState } from "react";
import { BarChart3, ChevronDown, MousePointerClick, Send, TrendingUp, Users } from "lucide-react";

import type { BehaviorMenuPayload, BehaviorTemplate, StateSnapshot } from "../types";

type AnalyticsBehavior = {
  behavior: BehaviorTemplate;
  title: string;
  baseline: number;
  post: number;
};

type CommitmentRow = {
  name: string;
  behaviorId: string;
  trigger: string;
  action: string;
  date: string;
};

const mockScores = [
  { baseline: 4.2, post: 7.6 },
  { baseline: 3.8, post: 7.2 },
  { baseline: 4.6, post: 7.9 }
];

const learnerNames = [
  "Jordan Reyes",
  "Priya Sharma",
  "Elena Park",
  "Marcus Liu",
  "Sofia Bennett",
  "Daniel Okafor",
  "Sam Patel",
  "Riya Chen",
  "Tasha Brooks",
  "Lena Park",
  "Diego Souza",
  "Maya Chen",
  "Thomas Wright",
  "Brooke Ellis",
  "Jonah Reed",
  "Amina Carter",
  "Victor Huang",
  "Nolan Price",
  "Imani Cole",
  "Grace Monroe"
];

const triggerPool = [
  "A discovery call starts",
  "A prospect shares a technical requirement",
  "A competitor comes up",
  "A deal enters stage 2",
  "I prepare for a demo",
  "A deal stalls after discovery"
];

function behaviorTitle(behavior: BehaviorTemplate, index: number): string {
  if (behavior.id === "pic_pbo_quantify_pain") return "Quantify Customer Pain";
  if (behavior.id === "pic_rc_capabilities_outcomes") return "Connect Photon DB to Required Outcomes";
  if (behavior.id === "pic_diff_differentiate") return "Differentiate Credibly vs. Competitors";
  return ["Quantify", "Connect", "Differentiate"][index] ?? behavior.name;
}

function commitmentAction(behavior: BehaviorTemplate): string {
  if (behavior.id === "pic_pbo_quantify_pain") {
    return "Quantify customer pain in business terms before advancing the deal";
  }
  if (behavior.id === "pic_rc_capabilities_outcomes") {
    return "Connect Photon DB capabilities to the required outcome in the recap";
  }
  if (behavior.id === "pic_diff_differentiate") {
    return "Differentiate with one credible proof point when competitors are named";
  }
  return `Apply ${behavior.name.toLowerCase()} before the next customer-facing step`;
}

function selectedBehaviors(menu: BehaviorMenuPayload, snapshot: StateSnapshot): BehaviorTemplate[] {
  const selectedIds = snapshot.selected_behavior_ids.length
    ? snapshot.selected_behavior_ids
    : menu.default_selected_behavior_ids;
  const fromIds = selectedIds
    .map((id) => menu.behaviors.find((behavior) => behavior.id === id))
    .filter((behavior): behavior is BehaviorTemplate => Boolean(behavior));
  return (fromIds.length >= 3 ? fromIds : menu.behaviors).slice(0, 3);
}

function buildCommitments(behaviors: BehaviorTemplate[]): CommitmentRow[] {
  return learnerNames.map((name, index) => {
    const behavior = behaviors[index % behaviors.length];
    return {
      name,
      behaviorId: behavior.id,
      trigger: triggerPool[index % triggerPool.length],
      action: commitmentAction(behavior),
      date: `Dec ${10 - Math.floor(index / 4)}, 2026`
    };
  });
}

export function AnalyticsDashboard({
  menu,
  snapshot
}: {
  menu: BehaviorMenuPayload;
  snapshot: StateSnapshot;
}) {
  const behaviors = useMemo(
    () =>
      selectedBehaviors(menu, snapshot).map((behavior, index) => ({
        behavior,
        title: behaviorTitle(behavior, index),
        baseline: mockScores[index]?.baseline ?? 4,
        post: mockScores[index]?.post ?? 7.3
      })),
    [menu, snapshot]
  );
  const commitments = useMemo(() => buildCommitments(behaviors.map((item) => item.behavior)), [behaviors]);
  const [filter, setFilter] = useState("all");
  const [visibleCount, setVisibleCount] = useState(10);
  const filteredCommitments = filter === "all"
    ? commitments
    : commitments.filter((row) => row.behaviorId === filter);
  const visibleCommitments = filteredCommitments.slice(0, visibleCount);

  return (
    <div className="analytics-dashboard">
      <header className="analytics-header">
        <div>
          <p className="eyebrow">Post-training pulse</p>
          <h1>Analytics</h1>
          <p>
            Mocked hackathon data for Photon DB, generated from the selected behavior set.
          </p>
        </div>
        <div className="analytics-header-badge">
          <BarChart3 size={18} />
          Mock post-training data
        </div>
      </header>

      <section className="analytics-section">
        <div className="section-header">
          <div>
            <p className="eyebrow">Level A</p>
            <h2>Behavior Change Deltas</h2>
          </div>
        </div>
        <div className="delta-grid">
          {behaviors.map((item) => (
            <DeltaCard key={item.behavior.id} item={item} />
          ))}
        </div>
      </section>

      <section className="analytics-section">
        <div className="section-header">
          <div>
            <p className="eyebrow">Level B</p>
            <h2>Nudge Engagement Analytics</h2>
          </div>
        </div>
        <div className="metric-grid">
          <MetricCard icon={<Send size={19} />} label="Overall Open Rate" value="94%" tone="green" />
          <MetricCard icon={<MousePointerClick size={19} />} label="Behaviors Applied" value="91" tone="copper" />
          <MetricCard icon={<Users size={19} />} label="Participants Engaged" value="86%" tone="blue" />
        </div>
      </section>

      <section className="analytics-section commitment-panel">
        <div className="commitment-header">
          <div>
            <p className="eyebrow">Level C</p>
            <h2>Commitment Statements</h2>
          </div>
          <label className="filter-label">
            Behavior filter
            <span className="select-wrap">
              <select
                value={filter}
                onChange={(event) => {
                  setFilter(event.target.value);
                  setVisibleCount(10);
                }}
              >
                <option value="all">All behaviors</option>
                {behaviors.map((item) => (
                  <option value={item.behavior.id} key={item.behavior.id}>{item.title}</option>
                ))}
              </select>
              <ChevronDown size={16} />
            </span>
          </label>
        </div>
        <div className="commitment-table-wrap">
          <table className="commitment-table">
            <thead>
              <tr>
                <th>Participant</th>
                <th>Behavior</th>
                <th>When</th>
                <th>I will</th>
                <th>Date submitted</th>
              </tr>
            </thead>
            <tbody>
              {visibleCommitments.map((row) => {
                const behavior = behaviors.find((item) => item.behavior.id === row.behaviorId);
                return (
                  <tr key={`${row.name}-${row.behaviorId}`}>
                    <td>{row.name}</td>
                    <td>{behavior?.title ?? "Behavior"}</td>
                    <td>{row.trigger}</td>
                    <td>{row.action}</td>
                    <td>{row.date}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        {visibleCount < filteredCommitments.length ? (
          <button
            className="button subtle load-more-button"
            type="button"
            onClick={() => setVisibleCount((count) => Math.min(count + 10, filteredCommitments.length))}
          >
            Load 10 more
          </button>
        ) : null}
      </section>
    </div>
  );
}

function DeltaCard({ item }: { item: AnalyticsBehavior }) {
  const delta = item.post - item.baseline;
  return (
    <article className="delta-card">
      <div className="delta-card-heading">
        <div>
          <h3>{item.title}</h3>
          <p>{item.behavior.name}</p>
        </div>
        <span className="delta-badge">
          <TrendingUp size={15} />
          +{delta.toFixed(1)}
        </span>
      </div>
      <ScoreBar label="Baseline" value={item.baseline} tone="soft" />
      <ScoreBar label="Post" value={item.post} tone="strong" />
    </article>
  );
}

function ScoreBar({ label, value, tone }: { label: string; value: number; tone: "soft" | "strong" }) {
  return (
    <div className="score-bar-row">
      <span>{label}</span>
      <div className="score-track">
        <div className={tone} style={{ width: `${Math.min(value * 10, 100)}%` }} />
      </div>
      <strong>{value.toFixed(1)}</strong>
    </div>
  );
}

function MetricCard({
  icon,
  label,
  value,
  tone
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  tone: "blue" | "copper" | "green";
}) {
  return (
    <article className={`metric-card ${tone}`}>
      <span>{icon}</span>
      <p>{label}</p>
      <strong>{value}</strong>
    </article>
  );
}
