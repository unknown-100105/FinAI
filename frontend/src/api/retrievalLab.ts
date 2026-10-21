const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export type RetrievalMode = "vectorless" | "hybrid" | "compare";

export type RetrievalEvidence = {
  document_id: number;
  title: string;
  source: string;
  date: string;
  text: string;
  lexical_score: number | null;
  semantic_score: number | null;
  fused_score: number | null;
};

export type RetrievalModeResult = {
  mode: string;
  status: "available" | "unavailable" | "error";
  latency_ms: number | null;
  result_count: number;
  results: RetrievalEvidence[];
  reason?: string;
};

export type RetrievalLabResponse = {
  query: string;
  top_k: number;
  mode: RetrievalMode;
  notice: string;
  results_by_mode: Record<string, RetrievalModeResult>;
};

export async function searchRetrievalLab(request: {
  query: string;
  mode: RetrievalMode;
  top_k?: number;
}): Promise<RetrievalLabResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/retrieval-lab/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...request, top_k: request.top_k ?? 5 }),
  });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Retrieval Lab API error ${response.status}: ${body}`);
  }
  return response.json() as Promise<RetrievalLabResponse>;
}
