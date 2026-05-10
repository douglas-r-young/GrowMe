import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, test, vi } from "vitest";

import App from "./App";
import { AssetLibrary } from "./components/AssetLibrary";
import type { StateSnapshot } from "./types";

const behaviors = [
  {
    id: "pic_pbo_quantify_pain",
    name: "Quantify customer pain in business impact terms",
    description: "Reps quantify pain.",
    framework_origin: "Command of the Message: PBO",
    research_questions: {}
  },
  {
    id: "pic_rc_capabilities_outcomes",
    name: "Connect product capabilities to required outcomes, not features",
    description: "Reps connect capability to outcome.",
    framework_origin: "Command of the Message: RC",
    research_questions: {}
  },
  {
    id: "pic_diff_differentiate",
    name: "Differentiate from named competitors with credible proof",
    description: "Reps differentiate with proof.",
    framework_origin: "Command of the Message: Diff",
    research_questions: {}
  }
];

const emptySnapshot: StateSnapshot = {
  session_uuid: "session-1",
  setup: {},
  wizard_inputs: null,
  selected_behavior_ids: [],
  enriched_context: null,
  design_doc: null,
  design_doc_edited_md: null,
  session_plan: null,
  program_assessment: null,
  deck: null,
  assessment_responses: [],
  commitments: {},
  checkins: {},
  nudges: [],
  delta_report: null,
  sim_complete: false,
  last_job: null,
  assets: []
};

const builtSnapshot: StateSnapshot = {
  ...emptySnapshot,
  setup: {
    program_name: "Photon DB discovery sprint",
    company_alias: "Photon DB",
    audience_preset: "Enterprise AEs"
  },
  selected_behavior_ids: behaviors.map((behavior) => behavior.id),
  program_assessment: {
    pre_questions: behaviors.map((behavior) => ({
      behavior_id: behavior.id,
      prompt: `How often do you ${behavior.name}?`,
      options: ["Never", "Rarely", "Sometimes", "Often", "Always"]
    })),
    commitment_options: []
  },
  deck: {
    session_number: 1,
    title: "Photon DB discovery sprint",
    behavior_ids: behaviors.map((behavior) => behavior.id),
    slides: [],
    facilitator_guide_md: "# Guide",
    manager_briefing_md: "# Briefing",
    pre_qr_url: "http://localhost:5173/?assessment=session-1&kind=pre",
    post_qr_url: "http://localhost:5173/?assessment=session-1&kind=post"
  },
  assets: [
    {
      id: "deck",
      name: "Session Deck",
      type: "Presentation",
      status: "Ready",
      description: "PowerPoint deck",
      download_url: "/api/sessions/session-1/downloads/deck"
    }
  ]
};

function mockFetch(handler: (url: string, init?: RequestInit) => unknown) {
  globalThis.fetch = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = input.toString();
    const body = handler(url, init);
    return {
      ok: true,
      status: 200,
      json: async () => body,
      text: async () => JSON.stringify(body)
    } as Response;
  });
}

describe("GrowMe React app", () => {
  beforeEach(() => {
    localStorage.clear();
    history.replaceState(null, "", "/");
    vi.restoreAllMocks();
  });

  test("renders Home by default with the hackathon sidebar and opens Step 1 from Add Program", async () => {
    mockFetch((url, init) => {
      if (url.endsWith("/api/sessions") && init?.method === "POST") {
        return { session_uuid: "session-1" };
      }
      if (url.endsWith("/api/behavior-menu")) {
        return { behaviors, default_selected_behavior_ids: behaviors.map((b) => b.id) };
      }
      if (url.endsWith("/api/sessions/session-1") && !init?.method) {
        return emptySnapshot;
      }
      return {};
    });

    render(<App />);

    expect(await screen.findByRole("heading", { name: /Current Programs/i })).toBeInTheDocument();
    for (const label of ["Home", "Analytics", "Settings", "Help Center", "Sign Out"]) {
      expect(screen.getByRole("button", { name: label })).toBeInTheDocument();
    }

    await userEvent.click(screen.getByRole("button", { name: /Add Program/i }));

    expect(await screen.findByRole("heading", { name: /Program Setup/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/Organization display name/i)).toHaveValue("Photon DB");
  });

  test("renders deterministic mocked Analytics and expands commitment statements", async () => {
    mockFetch((url, init) => {
      if (url.endsWith("/api/sessions") && init?.method === "POST") {
        return { session_uuid: "session-1" };
      }
      if (url.endsWith("/api/behavior-menu")) {
        return { behaviors, default_selected_behavior_ids: behaviors.map((b) => b.id) };
      }
      if (url.endsWith("/api/sessions/session-1") && !init?.method) {
        return builtSnapshot;
      }
      return {};
    });

    render(<App />);

    await screen.findByRole("heading", { name: /Current Programs/i });
    expect(screen.queryByText("Pre-survey")).not.toBeInTheDocument();
    expect(screen.queryByText("Commitment pick")).not.toBeInTheDocument();
    expect(screen.queryByText("Active session")).not.toBeInTheDocument();
    expect(screen.queryByText("session-")).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Analytics" }));

    expect(await screen.findByRole("heading", { name: /Behavior Change Deltas/i })).toBeInTheDocument();
    expect(screen.getByText(/Quantify customer pain in business impact terms/i)).toBeInTheDocument();
    expect(screen.getByText(/Connect product capabilities to required outcomes/i)).toBeInTheDocument();
    expect(screen.getByText(/Differentiate from named competitors/i)).toBeInTheDocument();
    expect(screen.getByText("94%")).toBeInTheDocument();
    expect(screen.getByText("91")).toBeInTheDocument();
    expect(screen.getByText("86%")).toBeInTheDocument();
    expect(screen.getByLabelText(/Behavior filter/i)).toBeInTheDocument();
    expect(screen.getAllByRole("row")).toHaveLength(11);

    await userEvent.click(screen.getByRole("button", { name: /Load 10 more/i }));

    expect(screen.getAllByRole("row")).toHaveLength(21);
  });

  test("saves setup through the API and advances to real behavior objectives", async () => {
    mockFetch((url, init) => {
      if (url.endsWith("/api/sessions") && init?.method === "POST") {
        return { session_uuid: "session-1" };
      }
      if (url.endsWith("/api/behavior-menu")) {
        return { behaviors, default_selected_behavior_ids: behaviors.map((b) => b.id) };
      }
      if (url.endsWith("/api/sessions/session-1") && !init?.method) {
        return emptySnapshot;
      }
      if (url.endsWith("/api/sessions/session-1/setup")) {
        return {
          ...emptySnapshot,
          setup: { company_alias: "Photon DB" },
          wizard_inputs: { audience_description: "Target audience: Enterprise AEs" }
        };
      }
      return {};
    });

    render(<App />);

    expect(await screen.findByRole("heading", { name: /Current Programs/i })).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /Add Program/i }));
    expect(await screen.findByRole("heading", { name: /Program Setup/i })).toBeInTheDocument();
    await userEvent.clear(screen.getByLabelText(/Organization display name/i));
    await userEvent.type(screen.getByLabelText(/Organization display name/i), "Photon DB");
    await userEvent.click(screen.getByRole("button", { name: /Continue to Training Objectives/i }));

    await waitFor(() => {
      expect(globalThis.fetch).toHaveBeenCalledWith(
        "/api/sessions/session-1/setup",
        expect.objectContaining({ method: "PUT" })
      );
    });
    expect(await screen.findByText(/Quantify customer pain/i)).toBeInTheDocument();
  });

  test("asset library only renders backend-provided assets", () => {
    render(
      <AssetLibrary
        sessionId="session-1"
        assets={[
          {
            id: "deck",
            name: "Session Deck",
            type: "Presentation",
            status: "Ready",
            description: "PowerPoint deck",
            download_url: "/api/sessions/session-1/downloads/deck"
          }
        ]}
      />
    );

    expect(screen.getByText("Session Deck")).toBeInTheDocument();
    expect(screen.queryByText(/Program Assessment/i)).not.toBeInTheDocument();
  });

  test("learner pre route submits frequency answers", async () => {
    history.replaceState(null, "", "/?assessment=session-1&kind=pre");
    mockFetch((url, init) => {
      if (url.endsWith("/api/assessment/session-1/config?kind=pre")) {
        return {
          kind: "pre",
          assessment: {
            pre_questions: behaviors.map((b) => ({
              behavior_id: b.id,
              prompt: `How often do you ${b.name}?`,
              options: ["Never", "Rarely", "Sometimes", "Often", "Always"]
            })),
            commitment_options: []
          }
        };
      }
      if (url.endsWith("/api/assessment/session-1/pre") && init?.method === "POST") {
        return { status: "recorded" };
      }
      return {};
    });

    render(<App />);

    expect(await screen.findByRole("heading", { name: /How often do you do these today/i })).toBeInTheDocument();
    await userEvent.type(screen.getByLabelText(/Your name/i), "Sam");
    await userEvent.type(screen.getByLabelText(/Email/i), "sam@example.com");
    for (const option of screen.getAllByLabelText("Often")) {
      await userEvent.click(option);
    }
    await userEvent.click(screen.getByRole("button", { name: /Submit/i }));

    await waitFor(() => {
      expect(globalThis.fetch).toHaveBeenCalledWith(
        "/api/assessment/session-1/pre",
        expect.objectContaining({ method: "POST" })
      );
    });
    expect(await screen.findByText(/response was recorded/i)).toBeInTheDocument();
  });
});
