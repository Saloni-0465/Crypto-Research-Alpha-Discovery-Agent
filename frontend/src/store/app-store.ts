import { create } from "zustand";

import { api } from "@/lib/api";
import type { AgentLog, Opportunity, Report, Signal } from "@/lib/types";

type LoadState = "idle" | "loading" | "error";

type AppState = {
  backend: { status: LoadState; env?: string; error?: string };
  agents: { status: LoadState; error?: string };
  lastRun?: { run_id: string; report_id?: string | null; notes?: string[] };

  opportunities: { status: LoadState; items: Opportunity[]; error?: string };
  signals: { status: LoadState; items: Signal[]; error?: string };
  reports: { status: LoadState; items: Report[]; error?: string };
  logs: { status: LoadState; items: AgentLog[]; error?: string; runFilter?: string };

  refreshAll: () => Promise<void>;
  refreshOpportunities: () => Promise<void>;
  refreshSignals: () => Promise<void>;
  refreshReports: () => Promise<void>;
  refreshLogs: (run_id?: string) => Promise<void>;
  checkHealth: () => Promise<void>;
  runAgents: () => Promise<void>;
};

function errMsg(e: unknown) {
  return e instanceof Error ? e.message : String(e);
}

export const useAppStore = create<AppState>((set, get) => ({
  backend: { status: "idle" },
  agents: { status: "idle" },
  opportunities: { status: "idle", items: [] },
  signals: { status: "idle", items: [] },
  reports: { status: "idle", items: [] },
  logs: { status: "idle", items: [] },

  async checkHealth() {
    set({ backend: { status: "loading" } });
    try {
      const h = await api.health();
      set({ backend: { status: "idle", env: h.env } });
    } catch (e) {
      set({ backend: { status: "error", error: errMsg(e) } });
    }
  },

  async refreshOpportunities() {
    set((s) => ({ opportunities: { ...s.opportunities, status: "loading" } }));
    try {
      const res = await api.opportunities({ limit: 25, offset: 0 });
      set({ opportunities: { status: "idle", items: res.items } });
    } catch (e) {
      set({ opportunities: { status: "error", items: [], error: errMsg(e) } });
    }
  },

  async refreshSignals() {
    set((s) => ({ signals: { ...s.signals, status: "loading" } }));
    try {
      const res = await api.signals({ limit: 80, offset: 0 });
      set({ signals: { status: "idle", items: res.items } });
    } catch (e) {
      set({ signals: { status: "error", items: [], error: errMsg(e) } });
    }
  },

  async refreshReports() {
    set((s) => ({ reports: { ...s.reports, status: "loading" } }));
    try {
      const res = await api.reports({ limit: 25, offset: 0 });
      set({ reports: { status: "idle", items: res.items } });
    } catch (e) {
      set({ reports: { status: "error", items: [], error: errMsg(e) } });
    }
  },

  async refreshLogs(run_id?: string) {
    const runFilter = run_id ?? get().logs.runFilter;
    set((s) => ({ logs: { ...s.logs, status: "loading", runFilter } }));
    try {
      const res = await api.logs({ limit: 250, offset: 0, run_id: runFilter });
      set({ logs: { status: "idle", items: res.items, runFilter } });
    } catch (e) {
      set({ logs: { status: "error", items: [], error: errMsg(e), runFilter } });
    }
  },

  async runAgents() {
    if (get().agents.status === "loading") return;
    set({ lastRun: undefined });
    set({ agents: { status: "loading" } });
    try {
      const res = await api.runAgents();
      set({ agents: { status: "idle" }, lastRun: res });
      await get().refreshAll();
      if (res.run_id) await get().refreshLogs(res.run_id);
    } catch (e) {
      const error = errMsg(e);
      set({ agents: { status: "error", error }, lastRun: { run_id: "error", notes: [error] } });
    }
  },

  async refreshAll() {
    await Promise.all([
      get().checkHealth(),
      get().refreshOpportunities(),
      get().refreshSignals(),
      get().refreshReports(),
    ]);
  },
}));
