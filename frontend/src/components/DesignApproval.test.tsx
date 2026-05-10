import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, test, vi } from "vitest";

import { DesignApproval } from "./DesignApproval";
import type { StateSnapshot } from "../types";

const baseSnapshot: StateSnapshot = {
  session_uuid: "session-1",
  setup: { audience_preset: "Enterprise AEs" },
  wizard_inputs: null,
  selected_behavior_ids: [],
  enriched_context: null,
  design_doc: {
    audience_section_md: "Audience details",
    behavior_objectives: [
      "Success = learners can quantify pain.",
      "Success = learners can connect capabilities to outcomes.",
      "Success = learners can differentiate with proof."
    ],
    integration_learning_objective: "Learners can run stronger discovery calls.",
    transfer_plan_md: [
      "Transfer plan",
      "",
      "**Trigger event:** The next discovery call with a prospect.",
      "",
      "* Week 1: Send a reminder email.",
      "* Week 2: Schedule a manager coaching call."
    ].join("\n"),
    full_markdown: "# Original design markdown"
  },
  design_doc_edited_md: "# Edited design markdown",
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

function renderDesignApproval(snapshot: StateSnapshot = baseSnapshot) {
  return render(
    <DesignApproval
      sessionId="session-1"
      snapshot={snapshot}
      onBack={vi.fn()}
      onSnapshot={vi.fn()}
      onContinue={vi.fn()}
    />
  );
}

function mockFetch(handler: (url: string, init?: RequestInit) => unknown) {
  globalThis.fetch = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const body = handler(input.toString(), init);
    return {
      ok: true,
      status: 200,
      json: async () => body,
      text: async () => JSON.stringify(body)
    } as Response;
  });
}

describe("DesignApproval", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  test("keeps editable markdown closed until edit is clicked and saves inline edits", async () => {
    mockFetch((url, init) => {
      if (url.endsWith("/api/sessions/session-1/design-doc") && init?.method === "PUT") {
        return baseSnapshot;
      }
      return {};
    });

    renderDesignApproval();

    expect(screen.queryByRole("textbox", { name: /Editable design markdown/i })).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /Edit design markdown/i }));
    const editor = screen.getByRole("textbox", { name: /Editable design markdown/i });
    expect(editor).toHaveValue("# Edited design markdown");

    await userEvent.clear(editor);
    await userEvent.type(editor, "# Updated markdown");
    await userEvent.click(screen.getByRole("button", { name: /Save edits/i }));

    await waitFor(() => {
      expect(globalThis.fetch).toHaveBeenCalledWith(
        "/api/sessions/session-1/design-doc",
        expect.objectContaining({
          method: "PUT",
          body: JSON.stringify({ markdown: "# Updated markdown" })
        })
      );
    });
  });

  test("shows transfer plan as a compact preview until expanded", async () => {
    renderDesignApproval();

    expect(screen.getByText("Transfer plan")).toBeInTheDocument();
    expect(screen.queryByText(/\*\*Trigger event:\*\*/i)).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /View full plan/i }));
    expect(screen.getByText(/\*\*Trigger event:\*\*/i)).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /Collapse transfer plan/i }));
    expect(screen.queryByText(/\*\*Trigger event:\*\*/i)).not.toBeInTheDocument();
  });

  test("reruns design from the editor and refreshes markdown with generated fallback", async () => {
    const refreshedSnapshot: StateSnapshot = {
      ...baseSnapshot,
      design_doc: {
        ...baseSnapshot.design_doc!,
        full_markdown: "# Fresh regenerated markdown"
      },
      design_doc_edited_md: null
    };
    mockFetch((url, init) => {
      if (url.endsWith("/api/sessions/session-1/design-jobs") && init?.method === "POST") {
        return { job_id: "job-1" };
      }
      if (url.endsWith("/api/jobs/job-1")) {
        return {
          job_id: "job-1",
          kind: "design",
          session_id: "session-1",
          status: "complete",
          messages: ["Design document ready."]
        };
      }
      if (url.endsWith("/api/sessions/session-1") && !init?.method) {
        return refreshedSnapshot;
      }
      return {};
    });

    renderDesignApproval();

    await userEvent.click(screen.getByRole("button", { name: /Edit design markdown/i }));
    await userEvent.click(screen.getByRole("button", { name: /Re-run design/i }));

    await waitFor(() => {
      expect(screen.getByRole("textbox", { name: /Editable design markdown/i })).toHaveValue(
        "# Fresh regenerated markdown"
      );
    });
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "/api/sessions/session-1/design-jobs",
      expect.objectContaining({ method: "POST" })
    );
  });
});
