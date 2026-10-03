const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export type FinAIModel = {
  model_id: string;
  model_name: string;
  role: string;
  capabilities: string[];
  enabled: boolean;
  configuration_note: string;
};

export async function getFinAIModels(capability = "financial_qa") {
  const response = await fetch(API_BASE_URL + "/api/v1/models?capability=" + encodeURIComponent(capability));
  if (!response.ok) throw new Error("Model registry API error " + response.status + ": " + await response.text());
  return response.json() as Promise<{models: FinAIModel[]}>;
}
