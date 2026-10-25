const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export type FinAIModel = {
  model_id: string;
  model_name: string;
  role: string;
  provider: string;
  capabilities: string[];
  enabled: boolean;
  configured: boolean;
  quality_tier: number;
  latency_tier: number;
  cost_tier: number;
  routing_priority: number;
  configuration_note: string;
};

export type ModelRoutePreview = {
  capability: string;
  selected_model: string;
  provider: string;
  reason: string;
  fallback_chain: string[];
  risk_level: string;
  policy: string;
  network_mode: string;
  data_sensitivity: string;
  allowed_providers: string[];
  constraints_applied: string[];
  execution_mode: string;
  resource_fit: boolean;
  resource_reason: string;
  hardware: {
    cpu_cores: number;
    ram_gb: number;
    vram_gb: number;
    storage_free_gb: number;
    cuda_available: boolean;
    platform: string;
  };
};

export async function getFinAIModels(capability?: string) {
  const suffix = capability ? "?capability=" + encodeURIComponent(capability) : "";
  const response = await fetch(API_BASE_URL + "/api/v1/models" + suffix);
  if (!response.ok) {
    throw new Error("FinAI model API error " + response.status + ": " + await response.text());
  }
  return response.json() as Promise<{ models: FinAIModel[] }>;
}

export async function previewModelRoute(input: {
  capability: string;
  risk_level: string;
  language: string;
  model_id?: string;
  network_mode?: string;
  data_sensitivity?: string;
  allowed_providers?: string[];
}) {
  const response = await fetch(API_BASE_URL + "/api/v1/models/route", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!response.ok) {
    throw new Error("FinAI routing API error " + response.status + ": " + await response.text());
  }
  return response.json() as Promise<ModelRoutePreview>;
}


export type HardwareResourceSnapshot = {
  hardware: {
    cpu_cores: number;
    ram_gb: number;
    vram_gb: number;
    storage_free_gb: number;
    cuda_available: boolean;
    platform: string;
  };
  local_models: Array<{
    model_id: string;
    model_name: string;
    resource: {
      execution_mode: string;
      resource_fit: boolean;
      reason: string;
      required_ram_gb: number;
      required_vram_gb: number;
      gpu_required: boolean;
    };
  }>;
  planning_note: string;
};

export async function getHardwareResources() {
  const response = await fetch(API_BASE_URL + "/api/v1/models/resources");
  if (!response.ok) {
    throw new Error("FinAI resource API error " + response.status + ": " + await response.text());
  }
  return response.json() as Promise<HardwareResourceSnapshot>;
}


export type LocalModelStatus = {
  status: string;
  provider: string;
  configured: boolean;
  probe_requested: boolean;
  reachable: boolean;
  model_available: boolean;
  model_id?: string | null;
  message: string;
};

export async function getLocalModelStatus(probe = false): Promise<LocalModelStatus> {
  const suffix = probe ? "?probe=true" : "";
  const response = await fetch(API_BASE_URL + "/api/v1/system/local-model-status" + suffix);
  if (!response.ok) {
    throw new Error("FinAI local model status error " + response.status + ": " + await response.text());
  }
  return response.json() as Promise<LocalModelStatus>;
}
