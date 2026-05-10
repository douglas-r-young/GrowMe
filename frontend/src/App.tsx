import { useEffect, useState } from "react";

import { api } from "./api";
import { DesignApproval } from "./components/DesignApproval";
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
        if (statePayload.deck) setStep(3);
        else if (statePayload.design_doc) setStep(2);
        else if (statePayload.selected_behavior_ids.length === 3) setStep(2);
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

  if (loading) return <LoadingScreen />;
  if (error || !sessionId || !menu || !snapshot) return <ErrorScreen message={error ?? "Could not load GrowMe."} />;

  return (
    <div className="app-shell">
      <aside className="side-rail">
        <p className="brand">GrowMe</p>
        <p className="side-title">Active session</p>
        <code>{sessionId.slice(0, 8)}</code>
        {snapshot.program_assessment ? (
          <div className="side-links">
            <a href={`/?assessment=${sessionId}&kind=pre`}>Pre-survey</a>
            <a href={`/?assessment=${sessionId}&kind=post`}>Commitment pick</a>
          </div>
        ) : null}
      </aside>
      <main>
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
              setSnapshot(await api.saveBehaviors(sessionId, ids));
              setStep(2);
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
      </main>
    </div>
  );
}
