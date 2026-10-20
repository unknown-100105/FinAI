import { useState } from "react";
import { Database, FileSearch, Gauge, GitCompare, Search, ShieldCheck } from "lucide-react";
import { searchRetrievalLab, type RetrievalLabResponse, type RetrievalMode } from "../api/retrievalLab";
import "./RetrievalLab.css";

const examples = [
  "RBI UPI payment dispute complaint rules",
  "home loan interest repayment",
  "credit card transaction security",
];

function ModeResults({ label, data }: { label: string; data: NonNullable<RetrievalLabResponse["results_by_mode"]>[string] }) {
  return (
    <section className="retrieval-results-panel">
      <div className="retrieval-panel-heading">
        <div><span className="retrieval-kicker">RETRIEVAL MODE</span><h2>{label}</h2></div>
        <span className={data.status === "available" ? "retrieval-status ready" : "retrieval-status"}>{data.status}</span>
      </div>
      {data.status === "available" ? (
        <>
          <div className="retrieval-metrics">
            <div><span>Latency</span><strong>{data.latency_ms ?? "—"} ms</strong></div>
            <div><span>Evidence chunks</span><strong>{data.result_count}</strong></div>
          </div>
          {data.results.length ? data.results.map((item, index) => (
            <article className="retrieval-evidence" key={String(item.document_id) + index}>
              <div className="retrieval-evidence-top">
                <span>#{index + 1} · ID {item.document_id}</span>
                <span>{item.source || "Unknown source"}{item.date ? " · " + item.date : ""}</span>
              </div>
              <h3>{item.title || "Untitled document chunk"}</h3>
              <p>{item.text}</p>
              <div className="retrieval-score-row">
                <span>{item.lexical_score != null ? "Lexical score: " + item.lexical_score.toFixed(4) : "Lexical score: —"}</span>
                <span>{item.semantic_score != null ? "Semantic score: " + item.semantic_score.toFixed(4) : "Semantic score: —"}</span>
                <span>{item.fused_score != null ? "RRF score: " + item.fused_score.toFixed(5) : "RRF score: —"}</span>
              </div>
            </article>
          )) : <div className="retrieval-empty">No matching indexed evidence. Try a more specific query.</div>}
        </>
      ) : (
        <div className="retrieval-unavailable">
          <strong>{data.status === "unavailable" ? "Retrieval assets unavailable" : "Retrieval error"}</strong>
          <p>{data.reason || "Check the API logs and local retrieval assets."}</p>
        </div>
      )}
    </section>
  );
}

export function RetrievalLab() {
  const [query, setQuery] = useState(examples[0]);
  const [mode, setMode] = useState<RetrievalMode>("compare");
  const [data, setData] = useState<RetrievalLabResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const runSearch = async () => {
    if (!query.trim() || busy) return;
    setBusy(true);
    setError("");
    try {
      setData(await searchRetrievalLab({ query: query.trim(), mode, top_k: 5 }));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Retrieval request failed.");
      setData(null);
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="retrieval-page">
      <header className="retrieval-hero">
        <div>
          <div className="retrieval-kicker"><Database size={13} /> FINAI RESEARCH WORKSPACE</div>
          <h1>Retrieval Lab</h1>
          <p>Compare embedding-free Vectorless RAG with FinAI's existing FTS5 + FAISS hybrid retrieval. Inspect retrieved evidence and timing before making any quality claims.</p>
        </div>
        <div className="retrieval-hero-mark"><GitCompare size={24} /></div>
      </header>

      <div className="retrieval-command">
        <label>Financial question or keywords
          <textarea value={query} onChange={(event) => setQuery(event.target.value)} rows={2} maxLength={1000} placeholder="Ask about an RBI circular, UPI disputes, loans…" />
        </label>
        <label>Retrieval mode
          <select value={mode} onChange={(event) => setMode(event.target.value as RetrievalMode)}>
            <option value="compare">Compare both</option>
            <option value="vectorless">Vectorless RAG only</option>
            <option value="hybrid">Hybrid RAG only</option>
          </select>
        </label>
        <button type="button" onClick={() => void runSearch()} disabled={busy || !query.trim()}>
          <Search size={15} /> {busy ? "Searching…" : "Run retrieval"}
        </button>
      </div>

      {error && <div className="retrieval-error">{error}</div>}

      <div className="retrieval-safety-note"><ShieldCheck size={15} /><span>Evidence retrieval only: this lab does not generate financial advice. Ranking scores are not probabilities, and retrieval alone does not establish factual correctness.</span></div>

      {data && (
        <div className={mode === "compare" ? "retrieval-results-grid compare" : "retrieval-results-grid"}>
          {(["vectorless", "hybrid"] as const).filter((key) => key in data.results_by_mode).map((key) => (
            <ModeResults key={key} label={key === "vectorless" ? "Vectorless RAG · FTS5" : "Hybrid RAG · FTS5 + FAISS"} data={data.results_by_mode[key]} />
          ))}
        </div>
      )}

      {!data && !busy && !error && (
        <div className="retrieval-empty-state">
          <FileSearch size={25} /><h2>Inspect evidence retrieval</h2>
          <p>Run a query to see source chunks, retrieval scores, result counts and latency. Compare both modes on the same query.</p>
          <div>{examples.map((example) => <button key={example} type="button" onClick={() => setQuery(example)}>{example}</button>)}</div>
        </div>
      )}

      <footer className="retrieval-footnote"><Gauge size={13} /> For meaningful benchmarks, use a fixed query set and report Recall@k, MRR, latency and source coverage. One interactive query is a demo, not an evaluation.</footer>
    </section>
  );
}
