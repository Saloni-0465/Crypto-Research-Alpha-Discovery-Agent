import type { AgentLog, Opportunity, Paged, Report, Signal } from "@/lib/types";

const BACKEND_BASE =
  process.env.NEXT_PUBLIC_BACKEND_BASE?.replace(/\/$/, "") ??
  "http://localhost:8000";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE?.replace(/\/$/, "") ??
  `${BACKEND_BASE}/api`;

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "content-type": "application/json", ...(init?.headers ?? {}) },
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${text || res.statusText}`);
  }
  return (await res.json()) as T;
}

export const api = {
  health: async () => {
    const res = await fetch(`${BACKEND_BASE}/healthz`, { cache: "no-store" });
    if (!res.ok) throw new Error(`Health ${res.status}`);
    return (await res.json()) as { ok: boolean; env: string };
  },
  fetchData: () => apiFetch<{ run_id: string; status: string }>("/fetch-data", { method: "POST" }),
  runAgents: () =>
    apiFetch<{
      run_id: string;
      report_id?: string | null;
      opportunities_created: number;
      signals_created: number;
      notes: string[];
    }>("/run-agents", { method: "POST" }),
  opportunities: (params?: { limit?: number; offset?: number }) =>
    apiFetch<Paged<Opportunity>>(
      `/opportunities?limit=${params?.limit ?? 25}&offset=${params?.offset ?? 0}`
    ),
  signals: (params?: { limit?: number; offset?: number; coin_symbol?: string; kind?: string }) => {
    const p = new URLSearchParams();
    p.set("limit", String(params?.limit ?? 50));
    p.set("offset", String(params?.offset ?? 0));
    if (params?.coin_symbol) p.set("coin_symbol", params.coin_symbol);
    if (params?.kind) p.set("kind", params.kind);
    return apiFetch<Paged<Signal>>(`/signals?${p.toString()}`);
  },
  reports: (params?: { limit?: number; offset?: number }) =>
    apiFetch<Paged<Report>>(`/reports?limit=${params?.limit ?? 25}&offset=${params?.offset ?? 0}`),
  report: (id: string) => apiFetch<Report>(`/reports/${id}`),
  logs: (params?: { limit?: number; offset?: number; run_id?: string; agent?: string; step?: string }) => {
    const p = new URLSearchParams();
    p.set("limit", String(params?.limit ?? 100));
    p.set("offset", String(params?.offset ?? 0));
    if (params?.run_id) p.set("run_id", params.run_id);
    if (params?.agent) p.set("agent", params.agent);
    if (params?.step) p.set("step", params.step);
    return apiFetch<Paged<AgentLog>>(`/logs?${p.toString()}`);
  },
  search: (q: string, k = 8) =>
    apiFetch<{ hits: Array<{ embedding_id: number; score: number; meta: Record<string, unknown> }> }>(
      `/search?q=${encodeURIComponent(q)}&k=${k}`
    ),
};
