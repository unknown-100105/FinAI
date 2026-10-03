import { useEffect, useMemo, useState } from "react";
import { Globe2, ShieldCheck, Search, RefreshCw, Database, Landmark, WalletCards, Activity, ArrowUpRight, AlertTriangle } from "lucide-react";
import { getEligibility, getGlobalCatalog, getPrediction, type Eligibility, type GlobalCountry, type GlobalAssetClass, type Prediction } from "../api/intelligence";
import { MarketSearchBox } from "./MarketSearchBox";
import "./GlobalInvestmentHub.css";

function safePercent(value: unknown) {
  const number = typeof value === "number" ? value : Number(value);
  return Number.isFinite(number) ? Math.round(number * 100) + "%" : "—";
}

function topFeatures(value: unknown) {
  if (!value) return [];
  if (Array.isArray(value)) {
    return value
      .map((item, index) => {
        const number = Number(item);
        return Number.isFinite(number) ? [String(index), number] as const : null;
      })
      .filter((item): item is readonly [string, number] => Boolean(item))
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3)
      .map(([key, score]) => key + " " + Math.round(score * 100) + "%");
  }
  if (typeof value === "object") {
    return Object.entries(value as Record<string, unknown>)
      .map(([key, score]) => [key, Number(score)] as const)
      .filter((item) => Number.isFinite(item[1]))
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3)
      .map(([key, score]) => key.replaceAll("_", " ") + " " + Math.round(score * 100) + "%");
  }
  return [];
}

export function GlobalInvestmentHub(){
  const [countries,setCountries]=useState<GlobalCountry[]>([]);
  const [assetClasses,setAssetClasses]=useState<GlobalAssetClass[]>([]);
  const [country,setCountry]=useState("US");
  const [asset,setAsset]=useState("government_bond");
  const [query,setQuery]=useState("");
  const [eligibility,setEligibility]=useState<Eligibility|null>(null);
  const [prediction,setPrediction]=useState<Prediction|null>(null);
  const [instrument,setInstrument]=useState("NIFTY 50");
  const [loading,setLoading]=useState(true);
  const [predictionBusy,setPredictionBusy]=useState(false);
  const [error,setError]=useState("");

  const loadCatalog=async()=>{
    setLoading(true);setError("");
    try{const data=await getGlobalCatalog();setCountries(data.countries);setAssetClasses(data.asset_classes)}
    catch(e){setError(e instanceof Error?e.message:"Unable to load global registry")}
    finally{setLoading(false)}
  };
  useEffect(()=>{void loadCatalog()},[]);
  useEffect(()=>{
    if(country&&asset)void getEligibility(country,asset)
      .then(setEligibility)
      .catch(e=>setError(e instanceof Error?e.message:"Eligibility lookup failed"))
  },[country,asset]);

  const runPrediction=async()=>{
    setPredictionBusy(true);setError("");
    try{setPrediction(await getPrediction(instrument,5))}
    catch(e){setPrediction(null);setError(e instanceof Error?e.message:"Prediction unavailable")}
    finally{setPredictionBusy(false)}
  };

  const filtered=useMemo(()=>countries.filter(c=>(c.country+" "+c.country_code+" "+c.region+" "+c.primary_market).toLowerCase().includes(query.toLowerCase())),[countries,query]);
  const selectedCountry=countries.find(c=>c.country_code===country);

  return <section className="global-page">
    <div className="global-hero">
      <div><div className="module-kicker"><Globe2 size={14}/> Global investment intelligence</div><h1>Global markets, with an Indian-investor context layer.</h1><p>Explore market registries and instrument-level eligibility checks. Access can depend on residency, FEMA/LRS, local rules, intermediary onboarding, tax and repatriation conditions.</p></div>
      <button className="market-refresh" type="button" onClick={()=>void loadCatalog()} disabled={loading}><RefreshCw size={14}/>{loading?"Loading registry":"Refresh registry"}</button>
    </div>
    {error&&<div className="module-error">{error}</div>}
    <div className="global-stats">
      <div><Globe2 size={16}/><strong>{countries.length}</strong><span>markets in registry</span></div>
      <div><Database size={16}/><strong>{assetClasses.length}</strong><span>asset classes</span></div>
      <div><ShieldCheck size={16}/><strong>India</strong><span>investor context</span></div>
      <div><Activity size={16}/><strong>{prediction ? "Live benchmark" : "On demand"}</strong><span>model arena</span></div>
    </div>
    <div className="global-layout">
      <section className="workspace-panel global-directory-panel">
        <div className="module-panel-head"><div><div className="module-kicker">Market directory</div><h2>Choose a market</h2></div><span className="source-chip">{filtered.length} matches</span></div>
        <div className="global-search"><Search size={14}/><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search country, exchange or region"/></div>
        <div className="country-grid">{filtered.map(c=><button type="button" key={c.country_code} className={country===c.country_code?"country-card active":"country-card"} onClick={()=>setCountry(c.country_code)}><div><strong>{c.country}</strong><span>{c.region} · {c.primary_market}</span></div><em>{c.currency}</em></button>)}</div>
      </section>
      <aside className="workspace-panel eligibility-panel">
        <div className="module-panel-head"><div><div className="module-kicker">01 · Investor eligibility</div><h2>{selectedCountry?.country||country}</h2></div><ShieldCheck size={17}/></div>
        <label className="global-label">Asset class<select value={asset} onChange={e=>setAsset(e.target.value)}>{assetClasses.map(a=><option key={a.id} value={a.id}>{a.label}</option>)}</select></label>
        {eligibility&&<><div className={"eligibility-status "+eligibility.status.toLowerCase()}>{eligibility.status}</div><p className="eligibility-summary">{eligibility.summary}</p><div className="check-list">{eligibility.checks.map(x=><div key={x}><ShieldCheck size={12}/>{x}</div>)}</div>{eligibility.verification_sources.length>0&&<div className="verification-links"><span>Official verification sources</span>{eligibility.verification_sources.map(x=><a key={x} href={x} target="_blank" rel="noreferrer">{new URL(x).hostname}<ArrowUpRight size={10}/></a>)}</div>}</>}
      </aside>
    </div>
    <section className="workspace-panel analyst-engine-panel">
      <div className="module-panel-head"><div><div className="module-kicker">02 · Quant research</div><h2>Model Arena</h2></div><span className="source-chip">Chronological validation</span></div>
      <div className="prediction-toolbar"><MarketSearchBox value={instrument} onSelect={setInstrument}/><button className="primary-module-button" type="button" onClick={()=>void runPrediction()} disabled={predictionBusy}><WalletCards size={13}/>{predictionBusy?"Running benchmark…":"Run model arena"}</button></div>
      {prediction&&<><div className="ensemble-card"><div><span>Ensemble direction</span><strong>{prediction.ensemble.direction}</strong></div><div><span>Probability up</span><strong>{safePercent(prediction.ensemble.probability_up)}</strong></div><div><span>Model agreement</span><strong>{safePercent(prediction.ensemble.confidence)}</strong></div><div><span>Validation</span><strong>{prediction.validation?.test_samples||0} samples</strong></div></div>
      <div className="model-table-wrap"><table className="model-table"><thead><tr><th>Model</th><th>Direction</th><th>Probability</th><th>Holdout accuracy</th><th>Weight</th><th>Top features</th></tr></thead><tbody>{prediction.models.map(m=><tr key={m.model_id}><td><strong>{m.model_id.replaceAll("_"," ")}</strong><small>{m.family}</small></td><td><span className={m.direction==="bullish"?"signal-positive":m.direction==="bearish"?"signal-negative":"source-chip"}>{m.direction}</span></td><td>{safePercent(m.probability_up)}</td><td>{safePercent(m.validation_accuracy)}</td><td>{safePercent(m.weight)}</td><td>{topFeatures(m.feature_importance).join(" · ")||"No stable attribution returned"}</td></tr>)}</tbody></table></div></>}
      {!prediction&&<div className="model-empty-state"><div><Activity size={20}/><strong>Benchmark on demand</strong><span>Run the arena to compare six model families on chronological holdout data. FinAI will not fabricate unavailable metrics.</span></div></div>}
      {prediction&&<div className="global-model-footnote"><AlertTriangle size={12}/> Historical validation describes the selected dataset; it does not establish future market performance.</div>}
    </section>
    <div className="global-disclaimer"><Landmark size={14}/><span><strong>Eligibility is instrument-specific.</strong> Verify current RBI/FEMA/LRS requirements, local market rules, intermediary onboarding, currency controls, tax and repatriation conditions before investing.</span></div>
  </section>
}
export default GlobalInvestmentHub;
