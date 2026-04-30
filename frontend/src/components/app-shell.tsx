"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Activity, Bot, Search, ShieldCheck, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { useAppStore } from "@/store/app-store";

export function AppShell({ children }: { children: React.ReactNode }) {
  const backend = useAppStore((s) => s.backend);
  const agents = useAppStore((s) => s.agents);
  const checkHealth = useAppStore((s) => s.checkHealth);
  const runAgents = useAppStore((s) => s.runAgents);
  const lastRun = useAppStore((s) => s.lastRun);

  const statusVariant =
    backend.status === "error"
      ? "danger"
      : backend.status === "loading"
      ? "secondary"
      : "success";

  return (
    <div className="min-h-dvh bg-zinc-50 text-zinc-900 dark:bg-black dark:text-zinc-50">
      <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
        <div className="absolute -top-40 left-1/2 h-[520px] w-[880px] -translate-x-1/2 rounded-full bg-gradient-to-r from-indigo-500/20 via-cyan-400/10 to-emerald-500/20 blur-3xl" />
      </div>

      <header className="sticky top-0 z-20 border-b border-zinc-200/80 bg-white/80 backdrop-blur dark:border-zinc-800 dark:bg-zinc-950/60">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="grid size-10 place-items-center rounded-xl bg-zinc-900 text-zinc-50 shadow-sm dark:bg-zinc-50 dark:text-zinc-900">
              <Sparkles className="size-5" />
            </div>
            <div className="leading-tight">
              <div className="flex items-center gap-2">
                <h1 className="text-sm font-semibold tracking-tight">
                  Autonomous Crypto Research Agent
                </h1>
                <Badge
                  variant={statusVariant as never}
                  className={cn(
                    "pointer-events-auto",
                    backend.status === "loading" && "animate-pulse"
                  )}
                >
                  {backend.status === "error"
                    ? "Backend down"
                    : backend.status === "loading"
                    ? "Checking"
                    : `Live (${backend.env ?? "ok"})`}
                </Badge>
              </div>
              <p className="text-xs text-zinc-600 dark:text-zinc-400">
                Multi-agent pipeline with explainable alpha signals.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={() => checkHealth()}>
              <Activity className="size-4" />
              Health
            </Button>
            <Button onClick={() => runAgents()} disabled={agents.status === "loading"}>
              <Bot className={cn("size-4", agents.status === "loading" && "animate-pulse")} />
              {agents.status === "loading" ? "Running" : "Run agents"}
            </Button>
          </div>
        </div>

        {lastRun?.run_id && lastRun.run_id !== "error" ? (
          <div className="border-t border-zinc-200/80 dark:border-zinc-800">
            <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-3 text-xs text-zinc-600 dark:text-zinc-400">
              <div className="flex items-center gap-2">
                <ShieldCheck className="size-4" />
                <span>
                  Latest run:{" "}
                  <span className="font-mono text-zinc-900 dark:text-zinc-50">
                    {lastRun.run_id}
                  </span>
                </span>
              </div>
              <Link
                href="#logs"
                className="pointer-events-auto inline-flex items-center gap-2 font-medium text-zinc-900 hover:underline dark:text-zinc-50"
              >
                <Search className="size-4" />
                Jump to explainability
              </Link>
            </div>
          </div>
        ) : null}
      </header>

      <motion.main
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25 }}
        className="mx-auto w-full max-w-7xl px-6 py-10"
      >
        {children}
      </motion.main>
    </div>
  );
}
