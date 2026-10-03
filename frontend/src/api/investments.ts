const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export type InvestmentProduct = {
  product_id: string;
  name: string;
  category: string;
  rate_percent?: number | null;
  tenure: string;
  payout: string;
  eligibility: string;
  liquidity: string;
  tax_note: string;
  risk_note: string;
  description: string;
  source: string;
  source_url: string;
  effective_from?: string | null;
  effective_to?: string | null;
};

export type MutualFundCategory = {
  category_id: string;
  name: string;
  group: string;
  description: string;
  what_to_check: string[];
};

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(API_BASE_URL + path);
  if (!response.ok) throw new Error(`FinAI investment API error ${response.status}: ${await response.text()}`);
  return response.json() as Promise<T>;
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(API_BASE_URL + path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error(`FinAI investment API error ${response.status}: ${await response.text()}`);
  return response.json() as Promise<T>;
}

export function getInvestmentCatalog() {
  return getJson<{
    meta: { rate_period: string; rate_source: string; rate_source_url: string; today: string; note: string };
    small_savings: InvestmentProduct[];
    mutual_fund_categories: MutualFundCategory[];
  }>("/api/v1/investments/catalog");
}

export function projectSip(body: {
  monthly_investment: number;
  annual_return_percent: number;
  years: number;
  annual_step_up_percent?: number;
  annual_inflation_percent?: number;
  target_corpus?: number;
}) {
  return postJson<{ status: string; result: Record<string, any> }>("/api/v1/investments/sip/plan", body);
}

export function projectFd(body: { principal: number; annual_rate_percent: number; years: number; compounding_per_year?: number }) {
  return postJson<{ status: string; result: Record<string, any> }>("/api/v1/investments/fd/plan", body);
}

export function priceBond(body: { face_value: number; coupon_rate_percent: number; yield_percent: number; years_to_maturity: number; coupon_frequency?: number }) {
  return postJson<{ status: string; result: Record<string, any> }>("/api/v1/investments/bond/price", body);
}

export function projectSmallSavings(body: { product_id: string; principal: number; years?: number }) {
  return postJson<{ status: string; result: Record<string, any> }>("/api/v1/investments/small-savings/project", body);
}
