const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export type ComplianceItem = {
  item_id: string;
  name: string;
  category: string;
  period: string;
  purpose: string;
  who_uses_it: string;
  key_inputs: string[];
  workflow: string[];
  official_url: string;
  source_name: string;
  status_note: string;
};

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(API_BASE_URL + path);
  if (!response.ok) {
    throw new Error(`FinAI compliance API error ${response.status}: ${await response.text()}`);
  }
  return response.json() as Promise<T>;
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(API_BASE_URL + path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`FinAI compliance API error ${response.status}: ${await response.text()}`);
  }
  return response.json() as Promise<T>;
}

export function getComplianceCatalog(category?: string) {
  const suffix = category ? `?category=${encodeURIComponent(category)}` : "";
  return getJson<{
    meta: Record<string, string>;
    items: ComplianceItem[];
  }>(`/api/v1/compliance/catalog${suffix}`);
}

export function searchCompliance(query: string) {
  return getJson<{ query: string; results: ComplianceItem[] }>(
    `/api/v1/compliance/search?query=${encodeURIComponent(query)}`,
  );
}

export function calculateCapitalGainWorksheet(body: {
  buy_value: number;
  sell_value: number;
  transfer_costs?: number;
  improvement_cost?: number;
}) {
  return postJson<{ status: string; result: Record<string, number> }>(
    "/api/v1/compliance/capital-gains/worksheet",
    body,
  );
}
