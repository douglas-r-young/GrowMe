import type { BehaviorMenuPayload, JobStatus, StateSnapshot } from "./types";

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    headers: init?.body ? { "Content-Type": "application/json", ...(init.headers ?? {}) } : init?.headers,
    ...init
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  async createSession() {
    return request<{ session_uuid: string }>("/api/sessions", { method: "POST" });
  },
  async behaviorMenu() {
    return request<BehaviorMenuPayload>("/api/behavior-menu");
  },
  async session(sessionId: string) {
    return request<StateSnapshot>(`/api/sessions/${sessionId}`);
  },
  async saveSetup(sessionId: string, payload: Record<string, unknown>) {
    return request<StateSnapshot>(`/api/sessions/${sessionId}/setup`, {
      method: "PUT",
      body: JSON.stringify(payload)
    });
  },
  async saveBehaviors(sessionId: string, selected_behavior_ids: string[]) {
    return request<StateSnapshot>(`/api/sessions/${sessionId}/behaviors`, {
      method: "PUT",
      body: JSON.stringify({ selected_behavior_ids })
    });
  },
  async createDesignJob(sessionId: string) {
    return request<{ job_id: string }>(`/api/sessions/${sessionId}/design-jobs`, { method: "POST" });
  },
  async saveDesignDoc(sessionId: string, markdown: string) {
    return request<StateSnapshot>(`/api/sessions/${sessionId}/design-doc`, {
      method: "PUT",
      body: JSON.stringify({ markdown })
    });
  },
  async createBuildJob(sessionId: string) {
    return request<{ job_id: string }>(`/api/sessions/${sessionId}/build-jobs`, { method: "POST" });
  },
  async job(jobId: string) {
    return request<JobStatus>(`/api/jobs/${jobId}`);
  },
  async assessmentConfig(sessionId: string, kind: string) {
    return request<Record<string, unknown>>(`/api/assessment/${sessionId}/config?kind=${kind}`);
  },
  async submitAssessment(sessionId: string, kind: "pre" | "final", payload: Record<string, unknown>) {
    return request<{ status: string }>(`/api/assessment/${sessionId}/${kind}`, {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },
  async submitPost(sessionId: string, payload: Record<string, unknown>) {
    return request<{ status: string }>(`/api/assessment/${sessionId}/post`, {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },
  async submitCheckin(sessionId: string, payload: Record<string, unknown>) {
    return request<{ status: string }>(`/api/assessment/${sessionId}/checkin`, {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },
  async sendWeek(sessionId: string, week: string) {
    return request<{ sent: number; errors: string[] }>(`/api/sessions/${sessionId}/nudges/send-week`, {
      method: "POST",
      body: JSON.stringify({ week })
    });
  },
  async runSimulation(sessionId: string) {
    return request<StateSnapshot>(`/api/sessions/${sessionId}/simulation`, { method: "POST" });
  }
};

export async function waitForJob(jobId: string, onUpdate: (job: JobStatus) => void): Promise<JobStatus> {
  for (;;) {
    const job = await api.job(jobId);
    onUpdate(job);
    if (job.status === "complete" || job.status === "error") {
      return job;
    }
    await new Promise((resolve) => window.setTimeout(resolve, 1000));
  }
}
