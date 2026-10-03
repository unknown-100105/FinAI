import { useEffect, useState } from "react";
import { CheckCircle2, FileSearch, RefreshCw, ShieldCheck, Workflow } from "lucide-react";
import { getXAITrace, listXAITraces, type XAITraceSummary } from "../api/xai";
import "./PlatformModules.css";

function pretty(value:unknown){return String(value ?? "—").replaceAll("_"," ");}

export function XAIExplorerHub(){
  const [traces,setTraces]=useState<XAITraceSummary[]>([]);
  const [selected,setSelected]=useState<any>(null);
  const [busy,setBusy]=useState(true);
  const [error,setError]=useState("");

  const load=async()=>{
    setBusy(true); setError("");
    try{
      const result=await listXAITraces();
      setTraces(result.traces||[]);
      if(result.traces?.[0]) setSelected(await getXAITrace(result.traces[0].trace_id));
    }catch(e){setError(e instanceof Error?e.message:"XAI trace feed unavailable.");}
    finally{setBusy(false);}
  };

  useEffect(()=>{void load();},[]);

  return <section className="module-page">
    <div className="module-hero">
      <div>
        <div className="module-kicker"><Workflow size={14}/> Explainable AI</div>
        <h1>See why FinAI answered what it answered.</h1>
        <p>Trace router decisions, policy, execution, retrieval, model generation, verification and final output for each assistant turn.</p>
      </div>
      <button className="market-refresh" type="button" onClick={()=>void load()} disabled={busy}><RefreshCw size={13}/> Refresh traces</button>
    </div>
    {error && <div className="module-error">{error}</div>}
    <div className="xai-layout">
      <section className="workspace-panel xai-list">
        <div className="module-panel-head"><div><div className="module-kicker"><FileSearch size={13}/> Trace history</div><h2>{traces.length} traces</h2></div><span className="source-chip">Read only</span></div>
        {busy?<div className="module-empty">Loading traces…</div>:traces.map(t=><button type="button" key={t.trace_id} className={selected?.trace_id===t.trace_id?"xai-trace-row active":"xai-trace-row"} onClick={()=>void getXAITrace(t.trace_id).then(setSelected).catch(e=>setError(e.message))}>
          <strong>{t.trace_id}</strong><span>{pretty(t.intent)} · {pretty(t.final_status)}</span>
        </button>)}
        {!busy&&!traces.length&&<div className="module-empty">No traces exist yet. Send a message in the Assistant.</div>}
      </section>
      <section className="workspace-panel xai-detail">
        {!selected?<div className="module-empty">Select a trace.</div>:
          <>
            <div className="module-panel-head"><div><div className="module-kicker">Trace</div><h2>{selected.trace_id}</h2></div><span className="source-chip"><ShieldCheck size={13}/> Evidence trail</span></div>
            <div className="xai-stage-grid">
              {["router","policy","execution_plan","rag","response_generation","session","final"].map((key)=><div className="xai-stage-card" key={key}><span>{pretty(key)}</span><strong>{selected[key]?"Captured":"Not recorded"}</strong></div>)}
            </div>
            <pre className="xai-json">{JSON.stringify(selected,null,2)}</pre>
            <div className="data-note"><CheckCircle2 size={12}/> This view exposes the stored trace; it does not alter the decision or underlying financial data.</div>
          </>}
      </section>
    </div>
  </section>;
}
export default XAIExplorerHub;
