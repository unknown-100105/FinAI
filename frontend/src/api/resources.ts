const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export type OfficialResource = {
  resource_id: string;
  name: string;
  category: string;
  subcategory: string;
  summary: string;
  who: string;
  current_status: string;
  official_url: string;
  form_url: string | null;
  authority: string;
  source_date: string;
  notes: string;
  form_fields: string[];
};

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(API_BASE_URL + path);
  if (!response.ok) throw new Error("Resources API error " + response.status + ": " + await response.text());
  return response.json() as Promise<T>;
}

export function getOfficialResources(category?: string) {
  const suffix = category ? "?category=" + encodeURIComponent(category) : "";
  return getJson<{count: number; items: OfficialResource[]}>("/api/v1/resources" + suffix);
}

export function searchOfficialResources(query: string) {
  return getJson<{query: string; results: OfficialResource[]}>("/api/v1/resources/search?query=" + encodeURIComponent(query));
}
