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
