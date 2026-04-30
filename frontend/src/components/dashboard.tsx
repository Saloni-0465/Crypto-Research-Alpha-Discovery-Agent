"use client";

import * as React from "react";
import { motion } from "framer-motion";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { AlertTriangle, Flame, ListChecks, ScrollText } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { useAppStore } from "@/store/app-store";

function scoreBadge(score: number) {
  if (score >= 0.75) return "success";
  if (score >= 0.55) return "secondary";
  if (score >= 0.35) return "warn";
  return "outline";
}

export function Dashboard() {
  const refreshAll = useAppStore((s) => s.refreshAll);
  const refreshLogs = useAppStore((s) => s.refreshLogs);
  const runAgents = useAppStore((s) => s.runAgents);

  const opps = useAppStore((s) => s.opportunities);
  const signals = useAppStore((s) => s.signals);
  const reports = useAppStore((s) => s.reports);
  const logs = useAppStore((s) => s.logs);
  const lastRun = useAppStore((s) => s.lastRun);

  const [searchQ, setSearchQ] = React.useState("");
  const [searchRes, setSearchRes] = React.useState<unknown | null>(null);
  const [searchErr, setSearchErr] = React.useState<string | null>(null);
  const [logsRunId, setLogsRunId] = React.useState("");

  React.useEffect(() => {
    void refreshAll();
  }, [refreshAll]);

  const topChart = React.useMemo(() => {
    return (opps.items ?? []).slice(0, 10).map((o) => ({
      symbol: o.coin.symbol,
      final: Number(o.final_score.toFixed(2)),
      momentum: Number(o.momentum_score.toFixed(2)),
      sentiment: Number(o.sentiment_score.toFixed(2)),
      liquidity: Number(o.liquidity_score.toFixed(2)),
      risk: Number(o.risk_score.toFixed(2)),
    }));
  }, [opps.items]);

  async function doSearch() {
    setSearchErr(null);
    setSearchRes(null);
    try {
      const res = await api.search(searchQ, 10);
      setSearchRes(res);
    } catch (e) {
      setSearchErr(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <AppShell>
      <Tabs defaultValue="overview" className="w-full">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-3">
            <TabsList>
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="opportunities">Opportunities</TabsTrigger>
              <TabsTrigger value="signals">Signals</TabsTrigger>
              <TabsTrigger value="reports">Reports</TabsTrigger>
              <TabsTrigger value="logs">Explainability</TabsTrigger>
              <TabsTrigger value="search">Semantic search</TabsTrigger>
            </TabsList>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="secondary" onClick={() => refreshAll()}>
              Refresh
            </Button>
            <Button onClick={() => runAgents()}>Run now</Button>
          </div>
        </div>

        <TabsContent value="overview">
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Top opportunities (score)</CardTitle>
                <CardDescription>
                  Ranked by the multi-agent pipeline (momentum, sentiment,
                  liquidity, credibility, and risk).
                </CardDescription>
              </CardHeader>
              <CardContent className="h-[320px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={topChart} margin={{ left: 8, right: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                    <XAxis dataKey="symbol" tickLine={false} axisLine={false} />
                    <YAxis
                      domain={[0, 1]}
                      tickLine={false}
                      axisLine={false}
                      tickFormatter={(v) => String(v)}
                    />
                    <Tooltip
                      contentStyle={{
                        borderRadius: 12,
                        border: "1px solid rgba(24,24,27,0.12)",
                      }}
                    />
                    <Bar dataKey="final" fill="#0ea5e9" radius={[8, 8, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <div className="grid gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Flame className="size-4" />
                    Pipeline status
                  </CardTitle>
                  <CardDescription>
                    Trigger runs via UI or let Celery Beat run in the background.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-zinc-600 dark:text-zinc-400">
                      Opportunities
                    </span>
                    <span className="font-medium">{opps.items.length}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-zinc-600 dark:text-zinc-400">
                      Signals
                    </span>
                    <span className="font-medium">{signals.items.length}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-zinc-600 dark:text-zinc-400">
                      Reports
                    </span>
                    <span className="font-medium">{reports.items.length}</span>
                  </div>
                  {lastRun?.run_id ? (
                    <div className="rounded-lg border border-zinc-200/70 bg-zinc-50 p-3 text-xs dark:border-zinc-800 dark:bg-zinc-900/30">
                      <div className="font-mono">{lastRun.run_id}</div>
                      <div className="mt-1 text-zinc-600 dark:text-zinc-400">
                        {lastRun.notes?.[0] ?? "Latest run completed."}
                      </div>
                    </div>
                  ) : null}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <ListChecks className="size-4" />
                    Quick actions
                  </CardTitle>
                </CardHeader>
                <CardContent className="flex flex-col gap-2">
                  <Button
                    variant="outline"
                    onClick={() => {
                      const id = lastRun?.run_id;
                      void refreshLogs(id);
                      document.getElementById("logs")?.scrollIntoView({
                        behavior: "smooth",
                      });
                    }}
                  >
                    View explainability logs
                  </Button>
                  <Button variant="secondary" onClick={() => runAgents()}>
                    Run pipeline
                  </Button>
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="opportunities">
          <Card>
            <CardHeader>
              <CardTitle>Opportunities</CardTitle>
              <CardDescription>
                Latest run only, sorted by final score. Click “Run agents” to generate a fresh set.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Coin</TableHead>
                    <TableHead>Score</TableHead>
                    <TableHead>Momentum</TableHead>
                    <TableHead>Sentiment</TableHead>
                    <TableHead>Liquidity</TableHead>
                    <TableHead>Risk</TableHead>
                    <TableHead>Reasoning</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {opps.items.map((o) => (
                    <TableRow key={o.id}>
                      <TableCell>
                        <div className="font-medium">{o.coin.symbol}</div>
                        <div className="text-xs text-zinc-600 dark:text-zinc-400">
                          {o.coin.name}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={scoreBadge(o.final_score) as never}>
                          {o.final_score.toFixed(2)}
                        </Badge>
                      </TableCell>
                      <TableCell>{o.momentum_score.toFixed(2)}</TableCell>
                      <TableCell>{o.sentiment_score.toFixed(2)}</TableCell>
                      <TableCell>{o.liquidity_score.toFixed(2)}</TableCell>
                      <TableCell
                        className={cn(
                          o.risk_score > 0.7 && "text-red-600 dark:text-red-400"
                        )}
                      >
                        {o.risk_score.toFixed(2)}
                      </TableCell>
                      <TableCell className="max-w-[520px]">
                        <div className="text-sm">{o.reasoning}</div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="signals">
          <Card>
            <CardHeader>
              <CardTitle>Signals</CardTitle>
              <CardDescription>
                Latest raw agent signals (sentiment, on-chain, pattern findings).
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Time</TableHead>
                    <TableHead>Coin</TableHead>
                    <TableHead>Agent</TableHead>
                    <TableHead>Kind</TableHead>
                    <TableHead>Score</TableHead>
                    <TableHead>Confidence</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {signals.items.map((s) => (
                    <TableRow key={s.id}>
                      <TableCell className="font-mono text-xs">
                        {new Date(s.ts).toISOString().slice(11, 19)}
                      </TableCell>
                      <TableCell>
                        <div className="font-medium">{s.coin.symbol}</div>
                        <div className="text-xs text-zinc-600 dark:text-zinc-400">
                          {s.coin.name}
                        </div>
                      </TableCell>
                      <TableCell>{s.agent}</TableCell>
                      <TableCell>{s.kind}</TableCell>
                      <TableCell>{s.score.toFixed(2)}</TableCell>
                      <TableCell>{s.confidence.toFixed(2)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="reports">
          <Card>
            <CardHeader>
              <CardTitle>Reports</CardTitle>
              <CardDescription>
                The pipeline produces a structured “Alpha Report” with top picks and evidence.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {reports.items.map((r) => (
                <motion.div
                  key={r.id}
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.15 }}
                  className="rounded-xl border border-zinc-200/70 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-950"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <div className="font-medium">{r.title}</div>
                      <div className="mt-1 text-xs text-zinc-600 dark:text-zinc-400">
                        {new Date(r.created_at).toLocaleString()}
                      </div>
                      <div className="mt-2 text-sm text-zinc-700 dark:text-zinc-300">
                        {r.summary}
                      </div>
                    </div>
                    <Button
                      variant="outline"
                      onClick={() => {
                        navigator.clipboard.writeText(JSON.stringify(r.payload, null, 2));
                      }}
                    >
                      Copy payload
                    </Button>
                  </div>
                  <pre className="mt-3 max-h-[240px] overflow-auto rounded-lg border border-zinc-200/70 bg-zinc-50 p-3 text-xs dark:border-zinc-800 dark:bg-zinc-900/30">
                    {JSON.stringify(r.payload, null, 2)}
                  </pre>
                </motion.div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="logs">
          <div id="logs" />
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <ScrollText className="size-4" />
                Explainability logs
              </CardTitle>
              <CardDescription>
                Every agent step logs structured input/output + timing. Filter by run_id for a full trace.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex flex-col gap-2 md:flex-row md:items-center">
                <Input
                  placeholder="run_id (optional)"
                  value={logsRunId}
                  onChange={(e) => setLogsRunId(e.target.value)}
                  className="md:max-w-lg"
                />
                <Button
                  variant="outline"
                  onClick={() => refreshLogs((logsRunId || "").trim() || undefined)}
                >
                  Load logs
                </Button>
                <Button
                  variant="secondary"
                  onClick={() =>
                    refreshLogs(lastRun?.run_id && lastRun.run_id !== "error" ? lastRun.run_id : undefined)
                  }
                >
                  Latest run
                </Button>
              </div>

              {logs.status === "error" ? (
                <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-200">
                  <AlertTriangle className="size-4" />
                  {logs.error}
                </div>
              ) : null}

              <div className="space-y-3">
                {logs.items.map((l) => (
                  <div
                    key={l.id}
                    className="rounded-xl border border-zinc-200/70 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-950"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge variant="outline">{l.agent}</Badge>
                        <Badge variant="secondary">{l.step}</Badge>
                        <Badge
                          variant={
                            l.severity === "error"
                              ? ("danger" as never)
                              : l.severity === "warn"
                              ? ("warn" as never)
                              : ("secondary" as never)
                          }
                        >
                          {l.severity}
                        </Badge>
                        {l.duration_ms != null ? (
                          <span className="text-xs text-zinc-600 dark:text-zinc-400">
                            {l.duration_ms}ms
                          </span>
                        ) : null}
                      </div>
                      <div className="font-mono text-xs text-zinc-600 dark:text-zinc-400">
                        {new Date(l.ts).toISOString()}
                      </div>
                    </div>
                    <div className="mt-3 grid grid-cols-1 gap-3 lg:grid-cols-2">
                      <pre className="max-h-[240px] overflow-auto rounded-lg border border-zinc-200/70 bg-zinc-50 p-3 text-xs dark:border-zinc-800 dark:bg-zinc-900/30">
                        {JSON.stringify(l.input, null, 2)}
                      </pre>
                      <pre className="max-h-[240px] overflow-auto rounded-lg border border-zinc-200/70 bg-zinc-50 p-3 text-xs dark:border-zinc-800 dark:bg-zinc-900/30">
                        {JSON.stringify(l.output, null, 2)}
                      </pre>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="search">
          <Card>
            <CardHeader>
              <CardTitle>Semantic search</CardTitle>
              <CardDescription>
                Uses Gemini embeddings + FAISS to find similar opportunities/reasoning in the latest run.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex flex-col gap-2 md:flex-row md:items-center">
                <Input
                  placeholder='Try: "bullish momentum with low risk"'
                  value={searchQ}
                  onChange={(e) => setSearchQ(e.target.value)}
                  className="md:max-w-xl"
                />
                <Button onClick={() => doSearch()}>Search</Button>
              </div>
              {searchErr ? (
                <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-200">
                  {searchErr}
                </div>
              ) : null}
              {searchRes ? (
                <pre className="max-h-[520px] overflow-auto rounded-lg border border-zinc-200/70 bg-zinc-50 p-3 text-xs dark:border-zinc-800 dark:bg-zinc-900/30">
                  {JSON.stringify(searchRes, null, 2)}
                </pre>
              ) : null}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </AppShell>
  );
}
