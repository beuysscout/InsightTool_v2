const BASE_URL = "http://localhost:8000/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${res.status}: ${body}`);
  }
  return res.json();
}

// --- Projects ---

export async function createProject(name: string) {
  return request("/projects", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
}

export async function listProjects() {
  return request("/projects");
}

export async function getProject(projectId: string) {
  return request(`/projects/${projectId}`);
}

export async function deleteProject(projectId: string) {
  return request(`/projects/${projectId}`, { method: "DELETE" });
}

// --- Guides ---

export async function uploadGuide(
  projectId: string,
  file: File,
  objective: string,
  researchGoals: string
) {
  const formData = new FormData();
  formData.append("file", file);

  const params = new URLSearchParams();
  if (objective) params.set("objective", objective);
  if (researchGoals) params.set("research_goals", researchGoals);

  const res = await fetch(
    `${BASE_URL}/projects/${projectId}/guide/upload?${params.toString()}`,
    { method: "POST", body: formData }
  );
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
  return res.json();
}

export async function getGuide(projectId: string) {
  return request(`/projects/${projectId}/guide`);
}

export async function updateGuide(projectId: string, guide: unknown) {
  return request(`/projects/${projectId}/guide`, {
    method: "PUT",
    body: JSON.stringify(guide),
  });
}

export async function lockGuide(projectId: string) {
  return request(`/projects/${projectId}/guide/lock`, { method: "POST" });
}

// --- Sessions ---

export async function uploadTranscript(projectId: string, file: File) {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(
    `${BASE_URL}/projects/${projectId}/sessions/upload`,
    { method: "POST", body: formData }
  );
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
  return res.json();
}

export async function listSessions(projectId: string) {
  return request(`/projects/${projectId}/sessions`);
}

export async function getSession(projectId: string, sessionId: string) {
  return request(`/projects/${projectId}/sessions/${sessionId}`);
}

export async function scanPii(
  projectId: string,
  sessionId: string,
  interviewerName?: string,
  participantName?: string
) {
  const body: Record<string, string> = {};
  if (interviewerName) body.interviewer_name = interviewerName;
  if (participantName) body.participant_name = participantName;
  return request(`/projects/${projectId}/sessions/${sessionId}/scan-pii`, {
    method: "POST",
    body: Object.keys(body).length ? JSON.stringify(body) : undefined,
  });
}

export async function anonymiseTranscript(
  projectId: string,
  sessionId: string,
  detections: unknown[]
) {
  return request(`/projects/${projectId}/sessions/${sessionId}/anonymise`, {
    method: "POST",
    body: JSON.stringify({ detections }),
  });
}

export async function organiseTranscript(
  projectId: string,
  sessionId: string
) {
  return request(`/projects/${projectId}/sessions/${sessionId}/organise`, {
    method: "POST",
  });
}

export async function extractThemes(projectId: string, sessionId: string) {
  return request(`/projects/${projectId}/sessions/${sessionId}/extract-themes`, {
    method: "POST",
  });
}

// --- Themes ---

export async function listAllThemes(projectId: string) {
  return request(`/projects/${projectId}/themes`);
}

export async function getSessionThemes(
  projectId: string,
  sessionId: string
) {
  return request(`/projects/${projectId}/themes/${sessionId}`);
}

export async function updateThemeStatus(
  projectId: string,
  sessionId: string,
  themeId: string,
  status: string,
  notes?: string
) {
  const params = new URLSearchParams({ status });
  if (notes) params.set("researcher_notes", notes);
  return request(
    `/projects/${projectId}/themes/${sessionId}/${themeId}/status?${params.toString()}`,
    { method: "PUT" }
  );
}
