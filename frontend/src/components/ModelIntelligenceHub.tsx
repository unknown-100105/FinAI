import { useEffect, useMemo, useState } from "react";
import { CheckCircle2, Cloud, Cpu, Gauge, RefreshCw, Route, ShieldCheck } from "lucide-react";
import {
  getFinAIModels,
  getHardwareResources,
  previewModelRoute,
  type FinAIModel,
  type ModelRoutePreview,
  type HardwareResourceSnapshot,
} from "../api/models";
import "./ModelIntelligenceHub.css";

const providerLabels: Record<string, string> = {
  openai: "OpenAI",
  gemini: "Google Gemini",
  anthropic: "Anthropic",
  mistral: "Mistral",
  openrouter: "OpenRouter",
  local: "Local / research",
};

const capabilities = [
  { id: "response_generation", label: "General response" },
  { id: "financial_qa", label: "Financial Q&A" },
  { id: "financial_reasoning", label: "Financial reasoning" },
];

function ProviderCard({ provider, models }: { provider: string; models: FinAIModel[] }) {
  const configured = models.some((model) => model.configured);
  return (
    <article className="ai-provider-card">
      <div className="ai-provider-icon"><Cloud size={15} /></div>
      <div className="ai-provider-copy">
        <strong>{providerLabels[provider] || provider}</strong>
        <span>{models.length} registered model{models.length === 1 ? "" : "s"}</span>
      </div>
      <div className={configured ? "ai-provider-status online" : "ai-provider-status"}>{configured ? "Configured" : "Key not set"}</div>
    </article>
  );
}

export default function ModelIntelligenceHub() {
  const [models, setModels] = useState<FinAIModel[]>([]);
  const [capability, setCapability] = useState("financial_qa");
  const [risk, setRisk] = useState("medium");
  const [language, setLanguage] = useState("English");
  const [networkMode, setNetworkMode] = useState("online");
  const [dataSensitivity, setDataSensitivity] = useState("standard");
  const [route, setRoute] = useState<ModelRoutePreview | null>(null);
  const [resources, setResources] = useState<HardwareResourceSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [routeLoading, setRouteLoading] = useState(false);
  const [error, setError] = useState("");

  const loadModels = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await getFinAIModels();
      setModels(data.models);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Model registry unavailable.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { void loadModels(); }, []);

  useEffect(() => {
    void getHardwareResources()
      .then(setResources)
      .catch((requestError) => {
        setError(requestError instanceof Error ? requestError.message : "Resource planner unavailable.");
      });
  }, []);

  const providers = useMemo(() => {
    const grouped = new Map<string, FinAIModel[]>();
    models.forEach((model) => {
      const list = grouped.get(model.provider) || [];
      list.push(model);
      grouped.set(model.provider, list);
    });
    return [...grouped.entries()];
  }, [models]);

  const enabledModels = models.filter((model) => model.enabled && model.configured);
  const activeCandidates = models.filter((model) => capability === "all" || model.capabilities.includes(capability));

  const runRoutePreview = async () => {
    setRouteLoading(true);
    setError("");
    try {
      setRoute(await previewModelRoute({ capability, risk_level: risk, language, network_mode: networkMode, data_sensitivity: dataSensitivity }));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to preview route.");
    } finally {
      setRouteLoading(false);
    }
  };

  useEffect(() => { void runRoutePreview(); }, [capability, risk, language, networkMode, dataSensitivity]);

  return (
    <section className="module-page model-intelligence-page">
      <div className="model-intelligence-hero">
        <div>
          <div className="module-kicker"><Cpu size={14} /> Multi-cloud model intelligence</div>
          <h1>One FinAI brain. Multiple model providers.</h1>
          <p>FinAI can select a capability-matched model, preserve an auditable fallback chain and keep the financial engines and verification layer provider-agnostic.</p>
        </div>
        <div className="model-intelligence-badge"><Route size={14} /> Policy-routed</div>
      </div>

      <div className="ai-provider-grid">
        {providers.map(([provider, items]) => <ProviderCard key={provider} provider={provider} models={items} />)}
      </div>

      <div className="ai-summary-grid">
        <div><span>Registered</span><strong>{models.length}</strong><small>model definitions</small></div>
        <div><span>Configured</span><strong>{enabledModels.length}</strong><small>models with active credentials</small></div>
        <div><span>Capability fit</span><strong>{activeCandidates.length}</strong><small>candidates for this task</small></div>
        <div><span>Architecture</span><strong>Failover</strong><small>provider-level resilience</small></div>
      </div>

      <div className="ai-route-workspace">
        <section className="workspace-panel">
          <div className="module-panel-head">
            <div><div className="module-kicker">01 · Route preview</div><h2>Adaptive execution planner</h2></div>
            <button className="secondary-module-button" type="button" onClick={() => void loadModels()} disabled={loading}><RefreshCw size={12} /> Refresh registry</button>
          </div>
          <p className="ai-muted">Choose the workload and risk level to see the model FinAI would select before any generation call is made.</p>
          <div className="ai-route-controls">
            <label>Network<select value={networkMode} onChange={(event) => setNetworkMode(event.target.value)}><option value="online">Online</option><option value="degraded">Degraded</option><option value="offline">Offline</option></select></label>
            <label>Data sensitivity<select value={dataSensitivity} onChange={(event) => setDataSensitivity(event.target.value)}><option value="public">Public</option><option value="standard">Standard</option><option value="financial">Financial</option><option value="restricted">Restricted</option></select></label>
            <label>Capability<select value={capability} onChange={(event) => setCapability(event.target.value)}>{capabilities.map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}</select></label>
            <label>Risk<select value={risk} onChange={(event) => setRisk(event.target.value)}><option>low</option><option>medium</option><option>high</option><option>critical</option></select></label>
            <label>Language<select value={language} onChange={(event) => setLanguage(event.target.value)}><option>English</option><option>Tamil</option><option>Telugu</option><option>Kannada</option><option>Malayalam</option></select></label>
          </div>
          {route && (
            <div className="ai-route-result">
              {routeLoading && <div className="ai-route-loading"><RefreshCw size={12} className="spin" /> Re-evaluating execution policy…</div>}
              <div className="ai-route-main"><div className="ai-route-icon"><Route size={16} /></div><div><span>Selected execution model</span><strong>{route.selected_model}</strong><small>{providerLabels[route.provider] || route.provider} · {route.execution_mode.replaceAll("_", " ")}</small><em className={route.resource_fit ? "ai-resource-fit" : "ai-resource-fallback"}>{route.resource_fit ? "Resource fit" : "Resource constraint"}</em><span className="ai-route-reason">{route.reason.replaceAll("_", " ")}</span></div></div>
              <div className="ai-constraint-strip"><span>{route.network_mode}</span><span>{route.data_sensitivity}</span>{route.constraints_applied.map((item) => <span key={item}>{item.replaceAll("_", " ")}</span>)}</div><div className="ai-fallback-chain">{route.fallback_chain.map((item, index) => <span key={item}><i>{index + 1}</i>{item}</span>)}</div>
            </div>
          )}
        </section>

        <aside className="workspace-panel">
          <div className="module-panel-head"><div><div className="module-kicker">02 · Provider matrix</div><h2>Configured model surface</h2></div><ShieldCheck size={15} /></div>
          {loading ? <div className="ai-empty">Loading model registry…</div> : (
            <div className="ai-model-table">
              {models.map((model) => (
                <div className="ai-model-row" key={model.model_id}>
                  <div className="ai-model-main"><strong>{model.model_name}</strong><span>{model.model_id} · {providerLabels[model.provider] || model.provider}</span></div>
                  <div className={model.configured ? "ai-key-chip ok" : "ai-key-chip"}>{model.configured ? <CheckCircle2 size={10} /> : null}{model.configured ? "Configured" : "Not configured"}</div>
                  <div className="ai-model-tiers"><span title="Quality"><Gauge size={10} /> Q{model.quality_tier}</span><span title="Latency">L{model.latency_tier}</span><span title="Cost">C{model.cost_tier}</span></div>
                </div>
              ))}
            </div>
          )}

          {resources && (
            <div className="ai-resource-panel">
              <div className="ai-resource-head"><div><div className="module-kicker">03 · Compute fabric</div><h3>Local resource fit</h3></div><Cpu size={14} /></div>
              <div className="ai-resource-grid">
                <div><span>CPU</span><strong>{resources.hardware.cpu_cores} cores</strong></div>
                <div><span>RAM</span><strong>{resources.hardware.ram_gb} GB</strong></div>
                <div><span>VRAM</span><strong>{resources.hardware.cuda_available ? resources.hardware.vram_gb + " GB free" : "Unavailable"}</strong></div>
                <div><span>Storage</span><strong>{resources.hardware.storage_free_gb} GB free</strong></div>
              </div>
              {resources.local_models.map((item) => (
                <div className="ai-resource-model" key={item.model_id}>
                  <div><strong>{item.model_name}</strong><span>{item.resource.execution_mode.replaceAll("_", " ")}</span></div>
                  <div className={item.resource.resource_fit ? "ai-key-chip ok" : "ai-key-chip"}>{item.resource.resource_fit ? <CheckCircle2 size={10} /> : null}{item.resource.resource_fit ? "Fits" : "Fallback"}</div>
                </div>
              ))}
              <small className="ai-resource-note">{resources.planning_note}</small>
            </div>
          )}
        </aside>
      </div>

      <div className="ai-system-note"><Cpu size={14} /><div><strong>Routing boundary</strong><span>This is a deterministic policy heuristic, not a learned benchmark. Model quality, latency and cost tiers are configuration metadata; live provider performance must be benchmarked separately before production routing decisions are promoted.</span></div></div>
      {error && <div className="ai-error">{error}</div>}
    </section>
  );
}
