export type BehaviorTemplate = {
  id: string;
  name: string;
  description: string;
  framework_origin: string;
  research_questions: Record<string, string>;
};

export type AssetRow = {
  id: string;
  name: string;
  type: string;
  status: string;
  description: string;
  download_url: string | null;
};

export type JobStatus = {
  job_id: string;
  kind: string;
  session_id: string;
  status: "queued" | "running" | "complete" | "error";
  messages: string[];
  error?: string | null;
};

export type DesignDoc = {
  audience_section_md: string;
  behavior_objectives: string[];
  integration_learning_objective: string;
  transfer_plan_md: string;
  full_markdown: string;
};

export type FrequencyQuestion = {
  behavior_id: string;
  prompt: string;
  options: string[];
};

export type ProgramAssessment = {
  pre_questions: FrequencyQuestion[];
  commitment_options: string[];
};

export type Slide = {
  title: string;
  body_md: string;
  kind: string;
  layout: string;
  qr_url?: string | null;
  qr_caption?: string | null;
  blocks: Record<string, unknown>;
  speaker_notes?: string;
  image_path?: string | null;
};

export type SessionDeck = {
  session_number: number;
  title: string;
  behavior_ids: string[];
  slides: Slide[];
  facilitator_guide_md: string;
  manager_briefing_md: string;
  pptx_path?: string | null;
  pre_qr_url: string;
  post_qr_url: string;
};

export type LastJobSnapshot = {
  id: string;
  kind: string;
  status: "queued" | "running" | "complete" | "error";
  error: string | null;
  messages: string[];
  updated_at: string;
};

export type StateSnapshot = {
  session_uuid: string;
  setup: Record<string, unknown>;
  wizard_inputs: { audience_description: string } | null;
  selected_behavior_ids: string[];
  enriched_context: unknown | null;
  design_doc: DesignDoc | null;
  design_doc_edited_md: string | null;
  session_plan: unknown | null;
  program_assessment: ProgramAssessment | null;
  deck: SessionDeck | null;
  assessment_responses: unknown[];
  commitments: Record<string, Record<string, unknown>>;
  checkins: Record<string, Array<[number, boolean]>>;
  nudges: unknown[];
  delta_report: { full_markdown: string } | null;
  sim_complete: boolean;
  last_job: LastJobSnapshot | null;
  assets: AssetRow[];
};

export type BehaviorMenuPayload = {
  behaviors: BehaviorTemplate[];
  default_selected_behavior_ids: string[];
};

export type CommitmentOption = {
  behavior_id: string;
  behavior_name: string;
  commitment_text: string;
};
