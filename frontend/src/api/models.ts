const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export type FinAIModel = {
  model_id: string;
  model_name: string;
  role: string;
  capabilities: string[];
  enabled: boolean;
  configuration_note: string;
};

export async function getFinAIModels(capability?: string) {
  const suffix = capability ? "?capability=" + encodeURIComponent(capability) : "";
  const response = await fetch(API_BASE_URL + "/api/v1/models" + suffix);
  if (!response.ok) {
    throw new Error("FinAI model API error " + response.status + ": " + await response.text());
  }
  return response.json() as Promise<{ models: FinAIModel[] }>;
}
