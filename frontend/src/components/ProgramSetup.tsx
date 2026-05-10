import { useState } from "react";
import { BookOpen, Loader2, PenLine, Target, Users } from "lucide-react";

import { PanelTitle } from "./shared";
import type { StateSnapshot } from "../types";

const audiencePresets = [
  "Enterprise AEs",
  "Mid-market AEs",
  "SDRs / BDRs",
  "Customer success managers",
  "Sales engineers",
  "Frontline managers",
  "Other (describe in notes)"
];
const cohortSizes = ["1-9 participants", "10-20 participants", "21-40 participants", "40+ participants"];
const formats = ["Single session (demo)", "Half day", "Multi-week cohort"];
const setupPlaceholder =
  "12 mid-market AEs, 1-3 yrs tenure. They run discovery calls but don't quantify pain in business-impact terms. The comp plan rewards velocity over qualification.";

export function ProgramSetup({
  snapshot,
  onContinue
}: {
  snapshot: StateSnapshot;
  onContinue: (payload: Record<string, unknown>) => Promise<void>;
}) {
  const setup = snapshot.setup ?? {};
  const [programName, setProgramName] = useState(String(setup.program_name ?? ""));
  const [companyUrl, setCompanyUrl] = useState(String(setup.company_url ?? "neon.tech"));
  const [companyAlias, setCompanyAlias] = useState(String(setup.company_alias ?? "Photon DB"));
  const [audiencePreset, setAudiencePreset] = useState(String(setup.audience_preset ?? audiencePresets[0]));
  const [cohort, setCohort] = useState(String(setup.audience_cohort ?? cohortSizes[1]));
  const [format, setFormat] = useState(String(setup.audience_program_fmt ?? formats[0]));
  const [notes, setNotes] = useState(String(setup.audience_notes ?? setupPlaceholder));
  const existingRefs = (setup.reference_urls as string[] | undefined) ?? [];
  const [referenceUrl, setReferenceUrl] = useState(existingRefs[0] ?? "");
  const [busy, setBusy] = useState(false);

  return (
    <form
      onSubmit={async (event) => {
        event.preventDefault();
        setBusy(true);
        await onContinue({
          program_name: programName,
          company_url: companyUrl,
          company_alias: companyAlias,
          audience_preset: audiencePreset,
          audience_cohort: cohort,
          audience_program_fmt: format,
          audience_notes: notes,
          reference_urls: referenceUrl ? [referenceUrl] : [],
          uploaded_file_names: []
        });
        setBusy(false);
      }}
    >
      <div className="setup-grid">
        <section className="panel">
          <PanelTitle icon={<BookOpen size={18} />} title="Organizational Context" />
          <label>
            Program name
            <input value={programName} onChange={(event) => setProgramName(event.target.value)} placeholder="e.g., Q2 leadership cohort" />
          </label>
          <label>
            Company URL
            <input value={companyUrl} onChange={(event) => setCompanyUrl(event.target.value)} />
          </label>
          <label>
            Organization display name
            <input value={companyAlias} onChange={(event) => setCompanyAlias(event.target.value)} />
          </label>
          <label>
            Reference URL
            <input value={referenceUrl} onChange={(event) => setReferenceUrl(event.target.value)} placeholder="https://..." />
            <small className="field-hint">Captured for the research pipeline alongside the company URL.</small>
          </label>
        </section>
        <section className="panel">
          <PanelTitle icon={<Users size={18} />} title="Audience and Format" />
          <label>
            Target audience
            <select value={audiencePreset} onChange={(event) => setAudiencePreset(event.target.value)}>
              {audiencePresets.map((item) => (
                <option key={item}>{item}</option>
              ))}
            </select>
          </label>
          <label>
            Cohort size
            <select value={cohort} onChange={(event) => setCohort(event.target.value)}>
              {cohortSizes.map((item) => (
                <option key={item}>{item}</option>
              ))}
            </select>
          </label>
          <label>
            Program format
            <select value={format} onChange={(event) => setFormat(event.target.value)}>
              {formats.map((item) => (
                <option key={item}>{item}</option>
              ))}
            </select>
          </label>
        </section>
      </div>
      <section className="panel wide-panel">
        <PanelTitle icon={<PenLine size={18} />} title="Additional Context" />
        <label>
          Program brief and special instructions
          <textarea value={notes} onChange={(event) => setNotes(event.target.value)} rows={5} />
        </label>
      </section>
      <div className="action-row">
        <button className="button primary" type="submit" disabled={busy}>
          {busy ? <Loader2 className="spin" size={17} /> : <Target size={17} />}
          Continue to Training Objectives
        </button>
      </div>
    </form>
  );
}
