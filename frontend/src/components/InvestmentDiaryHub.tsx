import { useCallback, useEffect, useMemo, useState } from "react";
import { BookMarked, ExternalLink, LineChart, Plus, RefreshCw, Save, Trash2 } from "lucide-react";
import { getMarketHistory, getMarketNews, getMarketQuote, type MarketBar } from "../api/market";
import { CandleChart } from "./CandleChart";
import "./PlatformModules.css";

type DiaryEntry = { id:string; date:string; asset:string; thesis:string; action:string; notes:string; price:string };

function diaryKey(){ return "finai-investment-diary-v3"; }

function summarize(bars:MarketBar[]){
  if(bars.length<2) return null;
  const first=bars[0].close,last=bars.at(-1)!.close;
  const ret=(last/first-1)*100;
  const avg=bars.reduce((s,b)=>s+Number(b.volume||0),0)/bars.length;
  const lastVolume=Number(bars.at(-1)?.volume||0);
  return {ret,volumeRatio:avg?lastVolume/avg:0};
}

export function InvestmentDiaryHub(){
  const [entries,setEntries]=useState<DiaryEntry[]>([]);
  const [asset,setAsset]=useState("TCS");
  const [action,setAction]=useState("Watch");
  const [price,setPrice]=useState("");
  const [thesis,setThesis]=useState("");
  const [notes,setNotes]=useState("");
  const [bars,setBars]=useState<MarketBar[]>([]);
  const [news,setNews]=useState<any[]>([]);
  const [quote,setQuote]=useState<any>(null);
  const [busy,setBusy]=useState(false);
  const [watchlist,setWatchlist]=useState<string[]>([]);
  const [watchData,setWatchData]=useState<Record<string,{price:number|null;return30:number|null;volumeRatio:number|null;trend:string;news:any[]}>>({});
  const [watchBusy,setWatchBusy]=useState(false);

  useEffect(()=>{
    try{
      setEntries(JSON.parse(localStorage.getItem(diaryKey())||"[]"));
      setWatchlist(JSON.parse(localStorage.getItem("finai.watchlist")||"[]"));
    }catch{ setEntries([]); setWatchlist([]); }
  },[]);
  const snapshot=useMemo(()=>summarize(bars),[bars]);

  const refresh = useCallback(async () => {
    setBusy(true);
    try{
      const end=new Date(),start=new Date();
      start.setDate(end.getDate()-30);
      const [q,h,n]=await Promise.all([
        getMarketQuote(asset),
        getMarketHistory(asset,start.toISOString(),end.toISOString(),"1d"),
        getMarketNews(asset,8),
      ]);
      setQuote(q.quote);setPrice(String(q.quote.price??""));setBars(h.bars);setNews(n.articles);
    } finally { setBusy(false); }
  }, [asset]);
  useEffect(() => { void refresh().catch(() => setBars([])); }, [refresh]);
  const refreshWatchlist = useCallback(async () => {
    if (!watchlist.length) return;
    setWatchBusy(true);
    const end = new Date();
    const start = new Date();
    start.setDate(end.getDate() - 30);
    const results = await Promise.allSettled(
      watchlist.map(async (symbol) => {
        const [q,h,n] = await Promise.all([
          getMarketQuote(symbol),
          getMarketHistory(symbol,start.toISOString(),end.toISOString(),"1d"),
          getMarketNews(symbol,4),
        ]);
        const snapshot = summarize(h.bars);
        return [symbol,{
          price: Number(q.quote.price ?? 0) || null,
          return30: snapshot?.ret ?? null,
          volumeRatio: snapshot?.volumeRatio ?? null,
          trend: snapshot ? (snapshot.ret > 0 ? "up" : snapshot.ret < 0 ? "down" : "flat") : "—",
          news: n.articles,
        }] as const;
      }),
    );
    const next: typeof watchData = {};
    results.forEach((result) => { if (result.status === "fulfilled") next[result.value[0]] = result.value[1]; });
    setWatchData(next);
    setWatchBusy(false);
  }, [watchlist]);
  useEffect(() => { void refreshWatchlist().catch(() => undefined); }, [refreshWatchlist]);


  const save=()=>{
    const entry:DiaryEntry={id:globalThis.crypto?.randomUUID?.()||String(Date.now()),date:new Date().toISOString(),asset,action,price,thesis,notes};
    const updated=[entry,...entries].slice(0,250);
    setEntries(updated);localStorage.setItem(diaryKey(),JSON.stringify(updated));
    setThesis("");setNotes("");
  };
  const remove=(id:string)=>{
    const updated=entries.filter(item=>item.id!==id);
    setEntries(updated);localStorage.setItem(diaryKey(),JSON.stringify(updated));
  };

  return <section className="module-page">
    <div className="module-hero">
      <div><div className="module-kicker"><BookMarked size={14}/> Personal investment diary</div>
      <h1>Record the thesis, then compare it with what actually happened.</h1>
      <p>Each diary entry is local to this browser. FinAI attaches a current market snapshot and contextual headlines for research; it does not place trades or claim a future price move.</p></div>
      <button className="market-refresh" type="button" onClick={()=>void refresh()} disabled={busy}><RefreshCw size={14}/> Refresh snapshot</button>
    </div>

    <section className="workspace-panel">
      <div className="module-panel-head"><div><div className="module-kicker">Watchlist intelligence</div><h2>{watchlist.length} tracked assets</h2></div><button className="market-refresh" type="button" onClick={()=>void refreshWatchlist()} disabled={watchBusy}><RefreshCw size={13}/> {watchBusy?"Scanning…":"Refresh watchlist"}</button></div>
      {watchlist.length ? <div className="watch-analysis-table-wrap"><table className="ticker-table"><thead><tr><th>Asset</th><th>Latest</th><th>30D return</th><th>Volume ratio</th><th>Trend</th><th>Context</th></tr></thead><tbody>{watchlist.map(symbol=>{
        const d=watchData[symbol];
        return <tr key={symbol} onClick={()=>setAsset(symbol)}><td><strong>{symbol}</strong></td><td>{d?.price ?? "—"}</td><td className={Number(d?.return30||0)>=0?"market-positive":"market-negative"}>{d?.return30==null?"—":d.return30.toFixed(2)+"%"}</td><td>{d?.volumeRatio==null?"—":d.volumeRatio.toFixed(2)+"×"}</td><td>{d?.trend||"—"}</td><td>{d?.news?.[0]?.title||"No headline returned"}</td></tr>;
      })}</tbody></table></div> : <div className="module-empty">Add instruments to Portfolio → Watchlist to analyze them here.</div>}
      <div className="data-note">This panel reports observed market/news context. It does not infer a certain future price or recommend a trade.</div>
    </section>

    <div className="diary-layout">
      <section className="workspace-panel">
        <div className="module-panel-head"><div><div className="module-kicker"><LineChart size={13}/> Research context</div><h2>{asset}</h2></div><span className="source-chip">{quote?.source||"market feed"}</span></div>
        <div className="diary-asset-row">{["TCS","INFY","RELIANCE","HDFCBANK","NIFTY 50","BTC","ETH"].map(x=><button key={x} type="button" className={asset===x?"active":""} onClick={()=>setAsset(x)}>{x}</button>)}</div>
        {quote&&<div className="scanner-summary"><div><span>Latest</span><strong>{quote.price}</strong></div><div><span>30D return</span><strong className={Number(snapshot?.ret||0)>=0?"market-positive":"market-negative"}>{snapshot?snapshot.ret.toFixed(2)+"%":"—"}</strong></div><div><span>Volume ratio</span><strong>{snapshot?snapshot.volumeRatio.toFixed(2)+"×":"—"}</strong></div></div>}
        <CandleChart bars={bars} height={300}/>
        <div className="detail-section"><div className="detail-section-title">Possible explanations to investigate</div><div className="criteria-list"><span>Observed trend: {snapshot?(snapshot.ret>0?"up":"down"):"—"} across this window.</span><span>Volume condition: {snapshot&&snapshot.volumeRatio>1.5?"elevated":"not unusually elevated"} relative to this sample.</span><span>Check filings, company announcements, macro news and index/sector movement before assigning a cause.</span></div></div>
        <div className="detail-section"><div className="detail-section-title">Contextual headlines</div>{news.map((item:any,index:number)=><a key={item.title+index} className="news-item" href={item.link||"#"} target="_blank" rel="noreferrer"><div><strong>{item.title}</strong><span>{item.publisher||"Source"} · {item.published_at||"latest"}</span></div><ExternalLink size={12}/></a>)}</div>
      </section>

      <section className="workspace-panel">
        <div className="module-panel-head"><div><div className="module-kicker"><Plus size={13}/> Diary entry</div><h2>Save your research state</h2></div></div>
        <label>Asset<input value={asset} onChange={e=>setAsset(e.target.value.toUpperCase())}/></label>
        <label>Action<select value={action} onChange={e=>setAction(e.target.value)}><option>Watch</option><option>Research</option><option>Buy</option><option>Sell</option><option>Hold</option><option>Avoid</option></select></label>
        <label>Reference price<input value={price} onChange={e=>setPrice(e.target.value)}/></label>
        <label>Thesis<textarea value={thesis} onChange={e=>setThesis(e.target.value)} placeholder="What are you testing?"/></label>
        <label>Notes<textarea value={notes} onChange={e=>setNotes(e.target.value)} placeholder="Evidence, assumptions, risk factors and next review date…"/></label>
        <button type="button" className="primary-module-button" onClick={save}><Save size={13}/> Save research entry</button>
        <div className="data-note">Local browser storage only. Export/backup your diary before clearing browser data.</div>
      </section>
    </div>

    <section className="workspace-panel">
      <div className="module-panel-head"><div><div className="module-kicker">Diary history</div><h2>{entries.length} entries</h2></div></div>
      <div className="diary-entry-list">{entries.map(entry=><article className="diary-entry" key={entry.id}><div className="diary-entry-head"><strong>{entry.asset}</strong><span>{new Date(entry.date).toLocaleString()} · {entry.action}</span><button type="button" onClick={()=>remove(entry.id)}><Trash2 size={12}/></button></div><div className="diary-entry-grid"><div><span>Price</span><strong>{entry.price||"—"}</strong></div><div><span>Thesis</span><p>{entry.thesis||"—"}</p></div><div><span>Notes</span><p>{entry.notes||"—"}</p></div></div></article>)}{!entries.length&&<div className="module-empty">No research entries yet.</div>}</div>
    </section>
  </section>;
}
export default InvestmentDiaryHub;
