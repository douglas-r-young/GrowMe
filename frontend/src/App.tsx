import { useEffect, useState } from "react";
import {
  BarChart3,
  CircleHelp,
  Home,
  LogOut,
  Settings,
  Sprout
} from "lucide-react";

import { api } from "./api";
import { AnalyticsDashboard } from "./components/AnalyticsDashboard";
import { DesignApproval } from "./components/DesignApproval";
import { HomeDashboard } from "./components/HomeDashboard";
import { LearnerRoute } from "./components/LearnerRoute";
import { ProgramMaterials } from "./components/ProgramMaterials";
import { ProgramSetup } from "./components/ProgramSetup";
import { TrainingObjectives } from "./components/TrainingObjectives";
import {
  ErrorScreen,
  LoadingScreen,
  StaleJobNotice,
  StepHeader
} from "./components/shared";
import type { BehaviorMenuPayload, StateSnapshot } from "./types";

type AppView = "home" | "program" | "analytics" | "settings" | "help" | "signout";

export default function App() {
  const params = new URLSearchParams(window.location.search);
  const assessment = params.get("assessment");
  if (assessment) {
    return <LearnerRoute sessionId={assessment} kind={params.get("kind") ?? "pre"} params={params} />;
  }
  return <FacilitatorApp />;
}

function FacilitatorApp() {
  const [sessionId, setSessionId] = useState<string | null>(localStorage.getItem("growme_session_id"));
  const [snapshot, setSnapshot] = useState<StateSnapshot | null>(null);
  const [menu, setMenu] = useState<BehaviorMenuPayload | null>(null);
  const [step, setStep] = useState(0);
  const [activeView, setActiveView] = useState<AppView>("home");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    async function boot() {
      try {
        setLoading(true);
        let id = sessionId;
        if (!id) {
          const created = await api.createSession();
          id = created.session_uuid;
          localStorage.setItem("growme_session_id", id);
          if (mounted) setSessionId(id);
        }
        const [menuPayload, statePayload] = await Promise.all([api.behaviorMenu(), api.session(id)]);
        if (!mounted) return;
        setMenu(menuPayload);
        setSnapshot(statePayload);
        setStep(inferStep(statePayload));
      } catch (exc) {
        if (mounted) setError(exc instanceof Error ? exc.message : String(exc));
      } finally {
        if (mounted) setLoading(false);
      }
    }
    void boot();
    return () => {
      mounted = false;
    };
  }, []);

  async function reload() {
    if (!sessionId) return;
    setSnapshot(await api.session(sessionId));
  }

  function openExistingProgram() {
    setStep(inferStep(snapshot));
    setActiveView("program");
  }

  function addProgram() {
    setStep(0);
    setActiveView("program");
  }

  if (loading) return <LoadingScreen />;
  if (error || !sessionId || !menu || !snapshot) return <ErrorScreen message={error ?? "Could not load GrowMe."} />;

  return (
    <div className="app-shell">
      <SideRail
        activeView={activeView}
        onNavigate={(view) => setActiveView(view)}
      />
      <main>
        {activeView === "home" ? (
          <HomeDashboard
            menu={menu}
            snapshot={snapshot}
            onAddProgram={addProgram}
            onOpenProgram={openExistingProgram}
            onViewAnalytics={() => setActiveView("analytics")}
          />
        ) : null}
        {activeView === "program" ? (
          <>
            <StepHeader step={step} />
            <StaleJobNotice lastJob={snapshot.last_job} />
            {step === 0 ? (
              <ProgramSetup
                snapshot={snapshot}
                onContinue={async (payload) => {
                  setSnapshot(await api.saveSetup(sessionId, payload));
                  setStep(1);
                }}
              />
            ) : null}
            {step === 1 ? (
              <TrainingObjectives
                menu={menu}
                snapshot={snapshot}
                onBack={() => setStep(0)}
                onContinue={async (ids) => {
                  const updated = await api.saveBehaviors(sessionId, ids);
                  setSnapshot(updated);
                  setStep(inferStep(updated));
                }}
              />
            ) : null}
            {step === 2 ? (
              <DesignApproval
                sessionId={sessionId}
                snapshot={snapshot}
                onBack={() => setStep(1)}
                onSnapshot={setSnapshot}
                onContinue={() => setStep(3)}
              />
            ) : null}
            {step === 3 ? (
              <ProgramMaterials
                sessionId={sessionId}
                snapshot={snapshot}
                onBack={() => setStep(2)}
                onReload={reload}
                onSnapshot={setSnapshot}
              />
            ) : null}
          </>
        ) : null}
        {activeView === "analytics" ? <AnalyticsDashboard menu={menu} snapshot={snapshot} /> : null}
        {activeView === "settings" ? <PlaceholderView title="Settings" /> : null}
        {activeView === "help" ? <PlaceholderView title="Help Center" /> : null}
        {activeView === "signout" ? <PlaceholderView title="Sign Out" /> : null}
      </main>
    </div>
  );
}

function inferStep(snapshot: StateSnapshot | null): number {
  if (!snapshot) return 0;
  if (snapshot.deck) return 3;
  if (snapshot.design_doc) return 2;
  if (snapshot.selected_behavior_ids.length === 3) return 2;
  return 0;
}

function SideRail({
  activeView,
  onNavigate
}: {
  activeView: AppView;
  onNavigate: (view: AppView) => void;
}) {
  const navItems = [
    { label: "Home", view: "home" as const, icon: <Home size={18} /> },
    { label: "Analytics", view: "analytics" as const, icon: <BarChart3 size={18} /> },
    { label: "Settings", view: "settings" as const, icon: <Settings size={18} /> },
    { label: "Help Center", view: "help" as const, icon: <CircleHelp size={18} /> },
    { label: "Sign Out", view: "signout" as const, icon: <LogOut size={18} /> }
  ];
  return (
    <aside className="side-rail">
      <div className="side-brand">
        <Sprout size={24} />
        <span>GrowMe</span>
      </div>
      <nav className="side-nav" aria-label="Primary navigation">
        {navItems.map((item) => (
          <button
            className={`side-nav-button ${activeView === item.view ? "active" : ""}`}
            type="button"
            key={item.view}
            onClick={() => onNavigate(item.view)}
          >
            {item.icon}
            {item.label}
          </button>
        ))}
      </nav>
    </aside>
  );
}

function PlaceholderView({ title }: { title: string }) {
  return (
    <section className="panel placeholder-panel">
      <p className="eyebrow">Hackathon placeholder</p>
      <h1>{title}</h1>
      <p>This tab is intentionally parked for the demo.</p>
    </section>
  );
}
