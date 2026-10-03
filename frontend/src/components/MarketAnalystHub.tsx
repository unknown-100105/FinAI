import { useEffect, useMemo, useState } from "react";
import { Activity, AlertTriangle, ExternalLink, Newspaper, Play, Pause, RefreshCw } from "lucide-react";
import { explainCandle, getMarketAnalyst, type CandleAnalysis } from "../api/marketAnalyst";
import { MarketSearchBox } from "./MarketSearchBox";
import { CandleChart } from "./CandleChart";
import type { MarketBar } from "../api/market";
import "./PlatformModules.css";

const ranges = [
  {id:"1D",days:1,defaultInterval:"5m"},
  {id:"5D",days:5,defaultInterval:"15m"},
  {id:"1M",days:30,defaultInterval:"1h"},
  {id:"3M",days:90,defaultInterval:"1d"},
  {id:"1Y",days:365,defaultInterval:"1d"},
];

function datesFor(days:number){
  const end=new Date(); const start=new Date(); start.setDate(end.getDate()-days);
  return {start:start.toISOString(),end:end.toISOString()};
}

function toMarketBars(candles:CandleAnalysis[]):MarketBar[]{
  return candles.map(c=>({symbol:"",timestamp:c.timestamp,open:c.open,high:c.high,low:c.low,close:c.close,volume:c.volume,source:"analyst"}));
}

export function MarketAnalystHub(){
  const [instrument,setInstrument]=useState("TCS");
  const [range,setRange]=useState("1D");
  const [interval,setInterval]=useState("5m");
  const [candles,setCandles]=useState<CandleAnalysis[]>([]);
  const [news,setNews]=useState<any[]>([]);
  const [selected,setSelected]=useState<number>(0);
  const [loading,setLoading]=useState(false);
  const [error,setError]=useState("");
  const [playing,setPlaying]=useState(false);
  const [scenario,setScenario]=useState<{scenarios:Array<{name:string;conditions_to_watch:string[];not_a_prediction:boolean}>;forecast_note:string}>({scenarios:[],forecast_note:""});\n  const [aiExplanation,setAiExplanation]=useState("");\n  const [aiBusy,setAiBusy]=useState(false);

  const rangeConfig=useMemo(()=>ranges.find(r=>r.id===range)??ranges[0],[range]);

  const load=async()=>{
    setLoading(true);setError("");
    try{
      const d=datesFor(rangeConfig.days);
      const result=await getMarketAnalyst(instrument,d.start,d.end,interval);
      setCandles(result.analysis.candles);
      setScenario(result.analysis.scenario ?? {scenarios:[],forecast_note:""});
      setNews(result.news||[]);
      setSelected(Math.max(0,result.analysis.candles.length-1));
    }catch(e){setCandles([]);setError(e instanceof Error?e.message:"Market analysis unavailable.");}
    finally{setLoading(false);}
  };

  useEffect(()=>{setInterval(rangeConfig.defaultInterval)},[range]);
  useEffect(()=>{void load()},[instrument,range,interval]);
  useEffect(()=>{
    if(!playing||!candles.length)return;
    const timer=window.setInterval(()=>setSelected(i=>i>=candles.length-1?0:i+1),700);
    return()=>window.clearInterval(timer);
  },[playing,candles.length]);

  const candle=candles[selected];
  const bars=useMemo(()=>toMarketBars(candles),[candles]);

  return <section className="module-page">
    <div className="module-hero">
      <div>
        <div className="module-kicker"><Activity size={14}/> Market analyst</div>
        <h1>Explain every candle, not just the chart.</h1>
        <p>FinAI calculates the observed OHLC anatomy, close-to-close move, wick/body structure, relative volume and contextual news for each selected candle. A possible driver is clearly separated from proven causality.</p>
      </div>
      <button className="market-refresh" type="button" onClick={()=>void load()} disabled={loading}><RefreshCw size={14}/> Refresh</button>
    </div>

    {error&&<div className="module-error">{error}</div>}

    <div className="workspace-panel analyst-toolbar">
      <div className="market-search-stack"><MarketSearchBox value={instrument} onSelect={setInstrument}/></div>
      <div className="range-tabs">{ranges.map(r=><button key={r.id} className={range===r.id?"active":""} type="button" onClick={()=>setRange(r.id)}>{r.id}</button>)}</div>
      <div className="range-tabs">{["1m","5m","15m","30m","1h","4h","1d"].map(v=><button key={v} className={interval===v?"active":""} type="button" disabled={(v==="1m"&&rangeConfig.days>7)||(v==="5m"&&rangeConfig.days>7)} onClick={()=>setInterval(v)}>{v}</button>)}</div>
      <button type="button" className="secondary-module-button" onClick={()=>setPlaying(v=>!v)}><span>{playing?<Pause size={13}/>:<Play size={13}/>}</span>{playing?"Pause replay":"Replay candles"}</button>
    </div>

    <section className="workspace-panel">
      <div className="module-panel-head"><div><div className="module-kicker">OHLCV</div><h2>{instrument} · {interval} · {candles.length} candles</h2></div><span className="source-chip">yfinance snapshot</span></div>
      <CandleChart bars={bars} height={390} selectedIndex={candle?.index} onSelect={setSelected} showVolume />
      <div className="analyst-slider"><input type="range" min="0" max={Math.max(0,candles.length-1)} value={selected} onChange={e=>setSelected(Number(e.target.value))}/><span>{candle?new Date(candle.timestamp).toLocaleString():"—"}</span></div>
    </section>

    <section className="workspace-panel scenario-panel">
      <div className="module-panel-head"><div><div className="module-kicker">Forward scenarios</div><h2>What to monitor next</h2></div><span className="source-chip">Not a price forecast</span></div>
      <div className="scenario-grid">{scenario.scenarios.map(item => <article className="scenario-card" key={item.name}><strong>{item.name}</strong><div>{item.conditions_to_watch.map(condition => <span key={condition}>• {condition}</span>)}</div></article>)}</div>
      <div className="data-note">{scenario.forecast_note}</div>
    </section>

    <div className="analyst-grid">
      <section className="workspace-panel">
        <div className="module-panel-head"><div><div className="module-kicker">Selected candle</div><h2>{candle?new Date(candle.timestamp).toLocaleString():"No candle"}</h2></div><span className={candle?.direction==="bullish"?"signal-positive":candle?.direction==="bearish"?"signal-negative":"source-chip"}>{candle?.direction||"—"}</span></div>
        {candle&&<div className="candle-fact-grid">
          {[
            ["Open",candle.open],["High",candle.high],["Low",candle.low],["Close",candle.close],
            ["Candle return",candle.return_percent==null?"—":candle.return_percent.toFixed(3)+"%"],
            ["Range",candle.range_percent==null?"—":candle.range_percent.toFixed(3)+"%"],
            ["Body / range",candle.body_percent_of_range.toFixed(1)+"%"],
            ["Upper wick / range",candle.upper_wick_percent_of_range.toFixed(1)+"%"],
            ["Lower wick / range",candle.lower_wick_percent_of_range.toFixed(1)+"%"],
            ["Relative volume",candle.relative_volume==null?"—":candle.relative_volume.toFixed(2)+"×"],
            ["5-candle trend",candle.trend_last_5],
          ].map(([a,b])=><div key={String(a)}><span>{a}</span><strong>{b}</strong></div>)}
        </div>}
        {candle&&<div className="detail-section"><div className="detail-section-title">What the candle shows</div><div className="criteria-list">{candle.observed_features.length?candle.observed_features.map(x=><span key={x}>• {x}</span>):<span>Normal OHLC movement without a strong standalone pattern flag.</span>}</div></div>}
        <div className="data-note"><AlertTriangle size={12}/> {candle?.causality_note||"Select a candle."}</div>
        {candle && <button type="button" className="primary-module-button" disabled={aiBusy} onClick={() => {
          setAiBusy(true); setAiExplanation("");
          void explainCandle({instrument,candle,context_news:news.slice(0,8)}).then(result => setAiExplanation(result.response || "No model explanation returned."))
            .catch(e => setAiExplanation(e instanceof Error ? e.message : "AI explanation unavailable."))
            .finally(() => setAiBusy(false));
        }}>{aiBusy ? "Reasoning about candle…" : "Generate AI explanation"}</button>}
        {aiExplanation && <div className="ai-explanation"><div className="detail-section-title">AI analyst note</div><p>{aiExplanation}</p></div>}
      </section>

      <section className="workspace-panel">
        <div className="module-panel-head"><div><div className="module-kicker">Possible drivers</div><h2>Why might this candle exist?</h2></div><span className="source-chip">Hypotheses, not proof</span></div>
        {candle?.possible_drivers_to_investigate.map(x=><div key={x} className="driver-row">{x}</div>)}
        <div className="detail-section"><div className="detail-section-title"><Newspaper size={12}/> Contextual news</div>
          {news.slice(0,8).map((item:any,i)=><a key={item.title+i} className="news-item" href={item.link||"#"} target="_blank" rel="noreferrer"><div><strong>{item.title}</strong><span>{item.publisher||"Source"} · {item.published_at||"latest"}</span></div><ExternalLink size={12}/></a>)}
          {!news.length&&<div className="module-empty">No contextual headlines returned.</div>}
        </div>
      </section>
    </div>
  </section>;
}
export default MarketAnalystHub;
