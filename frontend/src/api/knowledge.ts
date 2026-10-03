const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export type RegulationTopic = {
  topic_id: string;
  title: string;
  category: string;
  answer: string;
  steps: string[];
  authority: string;
  official_url: string;
  updated: string;
  caveat: string;
};

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(API_BASE_URL + path);
  if (!response.ok) throw new Error("Knowledge API error " + response.status + ": " + await response.text());
  return response.json() as Promise<T>;
}

export function getRegulationTopics(category?: string) {
  const suffix = category ? "?category=" + encodeURIComponent(category) : "";
  return getJson<{ count: number; items: RegulationTopic[] }>("/api/v1/knowledge/regulations" + suffix);
}

export function searchKnowledge(query: string) {
  return getJson<{ query: string; results: RegulationTopic[] }>("/api/v1/knowledge/search?query=" + encodeURIComponent(query));
}
