export type SwarmTradeRequest = {
  symbol: string;
  asset_class: "equity" | "option" | "future" | "crypto" | "forex";
  side: "auto" | "long" | "short";
  entry_price: number;
  stop_price: number;
  target_price: number;
  capital: number;
  risk_pct: number;
  open_position_risk_pct: number;
  current_daily_loss_pct: number;
  max_daily_loss_pct: number;
  max_leverage: number;
  margin_rate: number;
  multiplier: number;
  unit_step: number;
  fee_bps: number;
  slippage_bps: number;
  max_loss_per_unit?: number;
  tick_size?: number;
  tick_value?: number;
  pip_size?: number;
  pip_value_per_unit?: number;
  margin_per_unit?: number;
  min_reward_risk: number;
  agent_count: number;
  signals: Record<string, number>;
};

export type SwarmTradePlan = {
  status: string;
  decision: string;
  symbol?: string;
  asset_class?: string;
  direction: string;
  reason: string;
  agent_count: number;
  confidence?: number;
  consensus_score: number;
  votes: { long: number; short: number; flat: number };
  role_scores?: Record<string, number>;
  risk?: {
    risk_budget: number;
    effective_risk_pct: number;
    estimated_total_risk: number;
    estimated_notional: number;
    effective_leverage: number;
    reward_risk_ratio_after_costs: number;
  } | null;
  sizing?: { quantity: number; unit_step: number; entry_price: number; stop_price: number; target_price: number } | null;
  execution: { mode: string; order_submitted: boolean; fill_claimed: boolean; broker_connected?: boolean };
  warnings?: string[];
};

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export async function createSwarmTradePlan(request: SwarmTradeRequest): Promise<SwarmTradePlan> {
  const response = await fetch(`${API_BASE_URL}/api/v1/swarmtrade/plan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(`SwarmTrade API error ${response.status}: ${message}`);
  }
  return response.json() as Promise<SwarmTradePlan>;
}


export type PaperPosition = {
  position_id: string;
  account_id: string;
  symbol: string;
  asset_class: string;
  direction: "long" | "short";
  quantity: number;
  entry_price: number;
  stop_price: number;
  target_price: number;
  estimated_risk: number;
  status: "OPEN" | "CLOSED";
  opened_at: number;
  closed_at?: number | null;
  exit_price?: number | null;
  gross_pnl?: number | null;
  estimated_costs?: number | null;
  net_pnl?: number | null;
  close_reason?: string | null;
  risk_metadata?: Record<string, unknown>;
};

export type PaperAccountSnapshot = {
  account_id: string;
  label: string;
  currency: string;
  initial_capital: number;
  realized_pnl: number;
  equity_excluding_unrealized_pnl: number;
  daily_realized_pnl: number;
  daily_realized_loss_pct: number;
  open_position_risk: number;
  open_position_risk_pct: number;
  open_positions: PaperPosition[];
  open_position_count: number;
  paper_only: true;
  unrealized_pnl_included: false;
};

const paperUrl = (path: string) => `${API_BASE_URL}/api/v1/swarmtrade/paper${path}`;

export async function getPaperLedgerStatus(): Promise<{ enabled: boolean; status: string }> {
  const response = await fetch(paperUrl("/status"));
  if (!response.ok) throw new Error(`Paper ledger status error ${response.status}`);
  return response.json() as Promise<{ enabled: boolean; status: string }>;
}

export async function createPaperAccount(request: {
  label: string; currency: string; initial_capital: number;
}): Promise<PaperAccountSnapshot> {
  const response = await fetch(paperUrl("/accounts"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!response.ok) throw new Error(`Paper account creation error ${response.status}: ${await response.text()}`);
  return response.json() as Promise<PaperAccountSnapshot>;
}

export async function getPaperAccount(accountId: string): Promise<PaperAccountSnapshot> {
  const response = await fetch(paperUrl(`/accounts/${encodeURIComponent(accountId)}`));
  if (!response.ok) throw new Error(`Paper account read error ${response.status}: ${await response.text()}`);
  return response.json() as Promise<PaperAccountSnapshot>;
}

export async function listPaperPositions(
  accountId: string,
  status: "open" | "closed" | "all" = "all",
): Promise<{ account_id: string; status_filter: string; count: number; positions: PaperPosition[] }> {
  const response = await fetch(
    paperUrl(`/accounts/${encodeURIComponent(accountId)}/positions?status=${status}`),
  );
  if (!response.ok) throw new Error(`Paper position history error ${response.status}: ${await response.text()}`);
  return response.json() as Promise<{ account_id: string; status_filter: string; count: number; positions: PaperPosition[] }>;
}

export async function openPaperPosition(request: {
  account_id: string;
  idempotency_key: string;
  acknowledge_simulation_only: true;
  plan: SwarmTradeRequest;
}): Promise<{
  status: string; position_id: string; symbol: string; direction: string; quantity: number;
  entry_price: number; estimated_risk: number; idempotent_replay: boolean;
}> {
  const response = await fetch(paperUrl(`/accounts/${encodeURIComponent(request.account_id)}/positions`), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      idempotency_key: request.idempotency_key,
      acknowledge_simulation_only: request.acknowledge_simulation_only,
      plan: request.plan,
    }),
  });
  if (!response.ok) throw new Error(`Paper entry error ${response.status}: ${await response.text()}`);
  return response.json();
}

export async function closePaperPosition(request: {
  account_id: string; position_id: string; idempotency_key: string;
  exit_price: number; reason: "manual" | "stop" | "target" | "risk_control";
}): Promise<{ status: string; net_pnl: number; gross_pnl: number; estimated_costs: number; idempotent_replay: boolean }> {
  const response = await fetch(
    paperUrl(`/accounts/${encodeURIComponent(request.account_id)}/positions/${encodeURIComponent(request.position_id)}/close`),
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        idempotency_key: request.idempotency_key,
        exit_price: request.exit_price,
        reason: request.reason,
      }),
    },
  );
  if (!response.ok) throw new Error(`Paper exit error ${response.status}: ${await response.text()}`);
  return response.json();
}
