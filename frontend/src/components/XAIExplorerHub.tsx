import { useCallback, useEffect, useState } from "react";
import { CheckCircle2, FileSearch, RefreshCw, ShieldCheck, Workflow } from "lucide-react";
import { getXAITrace, listXAITraces, type XAITraceSummary } from "../api/xai";
import "./PlatformModules.css";

function pretty(value:unknown){return String(value ?? "—").replaceAll("_"," ");}

export function XAIExplorerHub(){
  const [traces,setTraces]=useState<XAITraceSummary[]>([]);
  const [selected,setSelected]=useState<any>(null);
  const [busy,setBusy]=useState(true);
  const [error,setError]=useState("");

  const fetchTraces=useCallback(async()=>{
    try{
      const result=await listXAITraces();
      const available = result.traces || [];
      setTraces(available);
      const currentTraceId = localStorage.getItem("finai.currentTraceId");
      const preferred = currentTraceId
        ? available.find((trace) => trace.trace_id === currentTraceId)
        : undefined;
      if (preferred) {
        setSelected(await getXAITrace(preferred.trace_id));
      } else if (available[0]) {
        setSelected(await getXAITrace(available[0].trace_id));
      }
    }catch(e){setError(e instanceof Error?e.message:"XAI trace feed unavailable.");}
    finally{setBusy(false);}
  }, []);

  const load = () => { setBusy(true); setError(""); void fetchTraces(); };

  // oxlint-disable-next-line react/set-state-in-effect -- Fetches persisted trace data asynchronously.
    useEffect(()=>{void fetchTraces();},[fetchTraces]);

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
              {["router","policy","execution","authority","tool","rag","model","claims","verification","session","final"].map((key)=><div className="xai-stage-card" key={key}><span>{pretty(key)}</span><strong>{selected[key]?"Captured":"Not recorded"}</strong></div>)}
            </div>
            <div className="xai-explanation-grid">
              <div><span>Intent</span><strong>{pretty(selected.router?.intent)}</strong><small>{pretty(selected.router?.reason)} · confidence {selected.router?.confidence ?? "—"}</small></div>
              <div><span>Authority</span><strong>{pretty(selected.authority?.authority_class)}</strong><small>{selected.authority?.authority_source ?? "—"}</small></div>
              <div><span>Execution</span><strong>{pretty(selected.execution?.execution_class)}</strong><small>{pretty(selected.execution?.capability)}</small></div>
              <div><span>Model</span><strong>{pretty(selected.model?.model_id)}</strong><small>{pretty(selected.model?.source)}</small></div>
              <div><span>Verification</span><strong>{selected.verification?.passed ? "Passed" : "Not passed"}</strong><small>{pretty(selected.verification?.mode)}</small></div>
              <div><span>Claims</span><strong>{selected.claims?.total_count ?? 0}</strong><small>{selected.claims?.all_verified ? "All verified" : "Claim verification not applicable / incomplete"}</small></div>
            </div>
            <pre className="xai-json">{JSON.stringify(selected,null,2)}</pre>
            <div className="data-note"><CheckCircle2 size={12}/> This view exposes the stored trace; it does not alter the decision or underlying financial data.</div>
          </>}
      </section>
    </div>
  </section>;
}
export default XAIExplorerHub;
