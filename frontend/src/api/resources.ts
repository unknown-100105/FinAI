const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export type OfficialResource = {
  resource_id: string;
  name: string;
  category: string;
  audience: string[];
  official_url: string;
  authority: string;
  description: string;
  form_title: string;
  form_fields: string[];
  current_source: boolean;
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

export function getResourceForm(resourceId: string) {
  return getJson<{
    resource_id: string;
    form_title: string;
    authority: string;
    official_url: string;
    fields: string[];
    values: Record<string, string>;
    draft_status: string;
  }>("/api/v1/resources/forms/" + encodeURIComponent(resourceId));
}
