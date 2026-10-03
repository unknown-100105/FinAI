const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function getJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(API_BASE_URL + path, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!response.ok) {
    throw new Error(`FinAI causal-risk API error ${response.status}: ${await response.text()}`);
  }
  return response.json() as Promise<T>;
}

export type CausalGraph = {
  nodes: Array<{ node_id: string; label: string; kind: string }>;
  edges: Array<{ source: string; target: string; weight: number; lag?: number; modality?: string }>;
  engine: string;
  semantics: string;
  learned_components_status: Record<string, string>;
};

export type CounterfactualResult = {
  systemic_stress: number;
  channels: { liquidity: number; equity: number; debt: number; portfolio: number };
  interventions: Record<string, number>;
  allocation: Record<string, number>;
  structural_model: {
    method: string;
    intervention_operator: string;
    node_values: Record<string, number>;
    edge_contributions: Array<{ source: string; target: string; input: number; weight: number; contribution: number }>;
  };
  explanation: {
    primary_path: string[];
    paths: Array<{ path: string[]; strength: number; type: string }>;
    statement: string;
  };
  validation: {
    allocation: { passed: boolean; errors: string[]; total_percent: number };
    shocks: { passed: boolean; errors: string[] };
    graph_errors: string[];
  };
  research_status: Record<string, string>;
  assumptions: string;
  tail_scenarios?: {
    method: string;
    gfnets_status: string;
    scenario_count: number;
    scenarios: Array<{ scenario_id: string; shock: Record<string, number>; tail_score: number }>;
  };
};

export function getCausalGraph() {
  return getJson<CausalGraph>("/api/v1/causal-risk/graph");
}

export function getCausalArchitecture() {
  return getJson<Record<string, unknown>>("/api/v1/causal-risk/architecture");
}

export function runCounterfactual(body: {
  shock: Record<string, number>;
  allocation: Record<string, number>;
  include_tail_scenarios?: boolean;
}) {
  return getJson<CounterfactualResult>("/api/v1/causal-risk/counterfactual", {
    method: "POST",
    body: JSON.stringify(body),
  });
}
