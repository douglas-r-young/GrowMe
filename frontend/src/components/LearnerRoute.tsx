import { useEffect, useState } from "react";

import { api } from "../api";
import { ErrorScreen, LoadingScreen, SimpleLearnerShell } from "./shared";
import type { CommitmentOption, ProgramAssessment } from "../types";

export function LearnerRoute({
  sessionId,
  kind,
  params
}: {
  sessionId: string;
  kind: string;
  params: URLSearchParams;
}) {
  const [config, setConfig] = useState<Record<string, unknown> | null>(null);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .assessmentConfig(sessionId, kind)
      .then(setConfig)
      .catch((exc) => setError(exc instanceof Error ? exc.message : String(exc)));
  }, [sessionId, kind]);

  useEffect(() => {
    if (kind !== "checkin") return;
    const learner = params.get("learner");
    const week = Number(params.get("week") ?? 1);
    const doneValue = params.get("done") === "yes";
    if (learner) {
      api
        .submitCheckin(sessionId, { learner, week, done: doneValue })
        .then(() => setDone(true))
        .catch((exc) => setError(String(exc)));
    }
  }, [kind, params, sessionId]);

  if (error) return <ErrorScreen message={error} />;
  if (kind === "checkin") return <SimpleLearnerShell title={done ? "Got it - thanks!" : "Logging check-in..."} />;
  if (!config) return <LoadingScreen />;
  if (kind === "post") return <PostCommitmentForm sessionId={sessionId} config={config} />;
  return <LikertForm sessionId={sessionId} kind={kind === "final" ? "final" : "pre"} config={config} />;
}

function LikertForm({
  sessionId,
  kind,
  config
}: {
  sessionId: string;
  kind: "pre" | "final";
  config: Record<string, unknown>;
}) {
  const assessment = config.assessment as ProgramAssessment;
  const [learnerName, setLearnerName] = useState("");
  const [learnerId, setLearnerId] = useState("");
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [done, setDone] = useState(false);
  return (
    <SimpleLearnerShell title={kind === "pre" ? "How often do you do these today?" : "How often do you do these now?"}>
      <form
        className="learner-form"
        onSubmit={async (event) => {
          event.preventDefault();
          await api.submitAssessment(sessionId, kind, {
            learner_name: learnerName,
            learner_id: learnerId,
            frequency_answers: answers
          });
          setDone(true);
        }}
      >
        <label>
          Your name
          <input value={learnerName} onChange={(event) => setLearnerName(event.target.value)} required />
        </label>
        <label>
          Email
          <input value={learnerId} onChange={(event) => setLearnerId(event.target.value)} required />
        </label>
        {assessment.pre_questions.map((question) => (
          <fieldset key={question.behavior_id}>
            <legend>{question.prompt}</legend>
            <div className="radio-row">
              {question.options.map((option) => (
                <label key={option}>
                  <input
                    type="radio"
                    name={question.behavior_id}
                    value={option}
                    onChange={() => setAnswers({ ...answers, [question.behavior_id]: option })}
                    required
                  />
                  {option}
                </label>
              ))}
            </div>
          </fieldset>
        ))}
        <button className="button primary" type="submit">Submit</button>
        {done ? <p className="status-message">Your response was recorded.</p> : null}
      </form>
    </SimpleLearnerShell>
  );
}

function PostCommitmentForm({
  sessionId,
  config
}: {
  sessionId: string;
  config: Record<string, unknown>;
}) {
  const options = config.commitment_options as CommitmentOption[];
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [behaviorId, setBehaviorId] = useState(options[0]?.behavior_id ?? "");
  const [done, setDone] = useState(false);
  return (
    <SimpleLearnerShell title="Choose one behavior to focus on">
      <form
        className="learner-form"
        onSubmit={async (event) => {
          event.preventDefault();
          await api.submitPost(sessionId, { learner_name: name, learner_email: email, behavior_id: behaviorId });
          setDone(true);
        }}
      >
        <label>
          Your name
          <input value={name} onChange={(event) => setName(event.target.value)} required />
        </label>
        <label>
          Email
          <input value={email} onChange={(event) => setEmail(event.target.value)} required />
        </label>
        <fieldset>
          <legend>Pick one commitment</legend>
          {options.map((option) => (
            <label className="choice-card" key={option.behavior_id}>
              <input
                type="radio"
                name="behavior"
                value={option.behavior_id}
                checked={behaviorId === option.behavior_id}
                onChange={() => setBehaviorId(option.behavior_id)}
              />
              <strong>{option.behavior_name}</strong>
              <span>{option.commitment_text}</span>
            </label>
          ))}
        </fieldset>
        <button className="button primary" type="submit">Submit</button>
        {done ? <p className="status-message">Your commitment was recorded.</p> : null}
      </form>
    </SimpleLearnerShell>
  );
}
