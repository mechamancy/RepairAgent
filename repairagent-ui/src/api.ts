const BASE = "http://localhost:8000";

export async function getConfig() {
  const res = await fetch(`${BASE}/api/config`);
  if (!res.ok) throw new Error("Failed to load config");
  return res.json();
}

export async function saveConfig(cfg: any) {
  const res = await fetch(`${BASE}/api/config`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(cfg),
  });
  if (!res.ok) throw new Error("Failed to save config");
  return res.json();
}

export async function getDefaultConfig() {
  const res = await fetch(`${BASE}/api/default-config`);
  if (!res.ok) throw new Error("Failed to load default config");
  return res.json();
}

export async function startRun(data: { modelName: string; bugListPath?: string }) {
  const res = await fetch(`${BASE}/api/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to start run");
  return res.json() as Promise<{ runId: string }>;
}

export async function getRun(id: string) {
  const res = await fetch(`${BASE}/api/run/${id}`);
  if (!res.ok) throw new Error("Failed to get run");
  return res.json() as Promise<{ status: string; logs: string }>;
}

export async function terminateRun(id: string) {
  const res = await fetch(`${BASE}/api/run/${id}/terminate`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to terminate run");
  return res.json() as Promise<{ status: string }>;
}

export async function setApiKey(apiKey: string) {
  const res = await fetch(`${BASE}/api/set-api-key`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ apiKey }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Failed to set API key: ${text}`);
  }
  return res.json() as Promise<{ status: string; message: string }>;
}
