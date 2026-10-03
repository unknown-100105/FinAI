import { useEffect, useMemo, useState } from "react";
import { Globe2, ShieldCheck, Search, RefreshCw, Database, Landmark, WalletCards } from "lucide-react";
import { getEligibility, getGlobalCatalog, getPrediction, type Eligibility, type GlobalCountry, type GlobalAssetClass, type Prediction } from "../api/intelligence";
import { MarketSearchBox } from "./MarketSearchBox";
import "./GlobalInvestmentHub.css";

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
  const [error,setError]=useState("");

  const loadCatalog=async()=>{setLoading(true);setError("");try{const data=await getGlobalCatalog();setCountries(data.countries);setAssetClasses(data.asset_classes)}catch(e){setError(e instanceof Error?e.message:"Unable to load global registry")}finally{setLoading(false)}};
  useEffect(()=>{void loadCatalog()},[]);
  useEffect(()=>{if(country&&asset)void getEligibility(country,asset).then(setEligibility).catch(e=>setError(e instanceof Error?e.message:"Eligibility lookup failed"))},[country,asset]);
  const runPrediction=async()=>{try{const result=await getPrediction(instrument,5);setPrediction(result)}catch(e){setPrediction(null);setError(e instanceof Error?e.message:"Prediction unavailable")}};
  const filtered=useMemo(()=>countries.filter(c=>(c.country+" "+c.country_code+" "+c.region+" "+c.primary_market).toLowerCase().includes(query.toLowerCase())),[countries,query]);
  const selectedCountry=countries.find(c=>c.country_code===country);

  return <section className="global-page">
    <div className="module-hero">
      <div><div className="module-kicker"><Globe2 size={14}/> Global investment intelligence</div><h1>One research layer for markets around the world.</h1><p>Explore equities, ETFs, sovereign debt, corporate bonds, deposits, funds, REITs and commodities. The eligibility panel is a verification workflow, not an execution recommendation.</p></div>
      <button className="market-refresh" type="button" onClick={()=>void loadCatalog()} disabled={loading}><RefreshCw size={14}/> Refresh registry</button>
    </div>
    {error&&<div className="module-error">{error}</div>}
    <div className="global-stats">
      <div><Globe2 size={16}/><strong>{countries.length}</strong><span>markets in registry</span></div>
      <div><Database size={16}/><strong>{assetClasses.length}</strong><span>asset classes</span></div>
      <div><ShieldCheck size={16}/><strong>India</strong><span>investor context</span></div>
    </div>
    <div className="global-layout">
      <section className="workspace-panel">
        <div className="module-panel-head"><div><div className="module-kicker">Market directory</div><h2>Global markets</h2></div><span className="source-chip">Research registry</span></div>
        <div className="global-search"><Search size={14}/><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search country, exchange or region"/></div>
        <div className="country-grid">{filtered.map(c=><button type="button" key={c.country_code} className={country===c.country_code?"country-card active":"country-card"} onClick={()=>setCountry(c.country_code)}><div><strong>{c.country}</strong><span>{c.primary_market}</span></div><em>{c.currency}</em></button>)}</div>
      </section>
      <aside className="workspace-panel eligibility-panel">
        <div className="module-panel-head"><div><div className="module-kicker">Indian investor check</div><h2>{selectedCountry?.country||country}</h2></div><ShieldCheck size={17}/></div>
        <label className="global-label">Asset class<select value={asset} onChange={e=>setAsset(e.target.value)}>{assetClasses.map(a=><option key={a.id} value={a.id}>{a.label}</option>)}</select></label>
        {eligibility&&<><div className={"eligibility-status "+eligibility.status.toLowerCase()}>{eligibility.status}</div><p className="eligibility-summary">{eligibility.summary}</p><div className="check-list">{eligibility.checks.map(x=><div key={x}><ShieldCheck size={12}/>{x}</div>)}</div>{eligibility.verification_sources.length>0&&<div className="verification-links">Official verification source{eligibility.verification_sources.length>1?"s":""}: {eligibility.verification_sources.map(x=><a key={x} href={x} target="_blank" rel="noreferrer">{new URL(x).hostname}</a>)}</div>}</>}
      </aside>
    </div>
    <section className="workspace-panel analyst-engine-panel">
      <div className="module-panel-head"><div><div className="module-kicker">Multi-model analyst</div><h2>Model Arena</h2></div><span className="source-chip">Chronological validation</span></div>
      <div className="prediction-toolbar"><MarketSearchBox value={instrument} onSelect={setInstrument}/><button className="primary-module-button" type="button" onClick={()=>void runPrediction()}><WalletCards size={13}/> Run model arena</button></div>
      {prediction&&<><div className="ensemble-card"><div><span>Ensemble direction</span><strong>{prediction.ensemble.direction}</strong></div><div><span>Probability up</span><strong>{prediction.ensemble.probability_up==null?"—":Math.round(prediction.ensemble.probability_up*100)+"%"}</strong></div><div><span>Model agreement</span><strong>{prediction.ensemble.confidence==null?"—":Math.round(prediction.ensemble.confidence*100)+"%"}</strong></div><div><span>Validation</span><strong>{prediction.validation?.test_samples||0} samples</strong></div></div>
      <div className="model-table-wrap"><table className="model-table"><thead><tr><th>Model</th><th>Direction</th><th>Probability</th><th>Holdout accuracy</th><th>Weight</th><th>Top features</th></tr></thead><tbody>{prediction.models.map(m=><tr key={m.model_id}><td><strong>{m.model_id.replaceAll("_"," ")}</strong><small>{m.family}</small></td><td>{m.direction}</td><td>{m.probability_up==null?"—":Math.round(m.probability_up*100)+"%"}</td><td>{m.validation_accuracy==null?"—":Math.round(m.validation_accuracy*100)+"%"}</td><td>{Math.round(m.weight*100)+"%"}</td><td>{Object.entries(m.feature_importance).sort((a,b)=>b[1]-a[1]).slice(0,3).map(([k,v])=>k+" "+Math.round(v*100)+"%").join(" · ")||"—"}</td></tr>)}</tbody></table></div></>}
      {!prediction&&<div className="module-empty large">Run the model arena for a real historical-data benchmark. FinAI will not display fabricated prediction metrics.</div>}
    </section>
    <div className="global-disclaimer"><Landmark size={14}/><span>Eligibility is instrument-specific. Before investing, verify current RBI/FEMA/LRS requirements, local market rules, intermediary onboarding, currency controls, tax and repatriation conditions.</span></div>
  </section>
}
export default GlobalInvestmentHub;
