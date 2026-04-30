export type Coin = {
  id: string;
  symbol: string;
  name: string;
  coingecko_id?: string | null;
};

export type Opportunity = {
  id: string;
  created_at: string;
  run_id?: string | null;
  final_score: number;
  momentum_score: number;
  sentiment_score: number;
  liquidity_score: number;
  risk_score: number;
  credibility_score: number;
  reasoning: string;
  evidence: Record<string, unknown>;
  coin: Coin;
};

export type Signal = {
  id: string;
  ts: string;
  agent: string;
  kind: string;
  score: number;
  confidence: number;
  data: Record<string, unknown>;
  coin: Pick<Coin, "id" | "symbol" | "name">;
};

export type Report = {
  id: string;
  created_at: string;
  title: string;
  summary: string;
  payload: Record<string, unknown>;
};

export type AgentLog = {
  id: string;
  run_id: string;
  agent: string;
  step: string;
  ts: string;
  severity: "debug" | "info" | "warn" | "error" | string;
  duration_ms?: number | null;
  coin_id?: string | null;
  input: Record<string, unknown>;
  output: Record<string, unknown>;
  meta: Record<string, unknown>;
};

export type Paged<T> = {
  items: T[];
  limit: number;
  offset: number;
};
