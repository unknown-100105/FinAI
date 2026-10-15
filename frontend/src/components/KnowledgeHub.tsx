import { useEffect, useMemo, useState } from "react";
import { BookOpen, ExternalLink, Globe2, Landmark, Search, ShieldCheck } from "lucide-react";
import { getRegulationTopics, searchKnowledge, type RegulationTopic } from "../api/knowledge";
import "./PlatformModules.css";

const categories = ["All", "Listing", "Foreign Investment", "Investment", "Investment Product", "SEBI Regulation", "Crypto Regulation", "Crypto Mechanics"];

export function KnowledgeHub() {
  const [category, setCategory] = useState("All");
  const [query, setQuery] = useState("");
  const [items, setItems] = useState<RegulationTopic[]>([]);
  const [selectedId, setSelectedId] = useState("list_equity_mainboard");
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const request = query.trim()
      ? searchKnowledge(query)
      : getRegulationTopics(category === "All" ? undefined : category);
    void request.then((data) => setItems("items" in data ? data.items : data.results))
      .catch((requestError) => setError(requestError instanceof Error ? requestError.message : "Knowledge catalogue unavailable."))
      .finally(() => setBusy(false));
  }, [category, query]);

  const selected = useMemo(
    () => items.find((item) => item.topic_id === selectedId) ?? items[0],
    [items, selectedId],
  );

  return (
    <section className="module-page">
      <div className="module-hero">
        <div>
          <div className="module-kicker"><BookOpen size={14} /> Finance knowledge & regulation</div>
          <h1>Learn how finance works — and how the Indian framework is organised.</h1>
          <p>Mechanisms, investment routes, listing paths, foreign investment, ETFs, crypto rules and official-source navigation in one searchable workspace.</p>
        </div>
        <div className="module-orb"><Globe2 size={23} /></div>
      </div>

      {error && <div className="module-error">{error}</div>}

      <div className="compliance-toolbar">
        <div className="compliance-search"><Search size={15} /><input value={query} onChange={(event) => { setBusy(true); setQuery(event.target.value); }} placeholder="Search IPO, FPI, FDI, ETF, Bitcoin, mining, SEBI…" /></div>
        {!query && <div className="compliance-categories">{categories.map((item) => <button type="button" key={item} className={category === item ? "active" : ""} onClick={() => { if (category !== item) setBusy(true); setCategory(item); }}>{item}</button>)}</div>}
      </div>

      <div className="compliance-layout">
        <section className="workspace-panel compliance-list-panel">
          <div className="module-panel-head">
            <div><div className="module-kicker"><Landmark size={13} /> Topics</div><h2>{items.length} knowledge routes</h2></div>
            <span className="source-chip"><ShieldCheck size={13} /> Source-linked</span>
          </div>
          {busy ? <div className="module-empty">Loading knowledge…</div> :
            items.length ? items.map((item) => (
              <button type="button" className={selected?.topic_id === item.topic_id ? "compliance-row active" : "compliance-row"} key={item.topic_id} onClick={() => setSelectedId(item.topic_id)}>
                <div><strong>{item.title}</strong><span>{item.category} · {item.updated}</span></div>
                <small>{item.answer}</small>
              </button>
            )) : <div className="module-empty">No matching topic.</div>}
        </section>

        <section className="workspace-panel compliance-detail">
          {selected ? (
            <>
              <div className="module-panel-head">
                <div><div className="module-kicker">{selected.category}</div><h2>{selected.title}</h2></div>
                <a className="source-link" href={selected.official_url} target="_blank" rel="noreferrer">Official source <ExternalLink size={12} /></a>
              </div>
              <p className="compliance-purpose">{selected.answer}</p>
              <div className="detail-section">
                <div className="detail-section-title">Practical workflow</div>
                <div className="workflow-list">{selected.steps.map((step, index) => <div key={step}><b>{String(index + 1).padStart(2, "0")}</b><span>{step}</span></div>)}</div>
              </div>
              <div className="platform-banner"><ShieldCheck size={15} /><div><strong>Authority: {selected.authority}</strong><span>Source/update: {selected.updated} · {selected.caveat}</span></div></div>
            </>
          ) : <div className="module-empty">Select a topic.</div>}
        </section>
      </div>
    </section>
  );
}

export default KnowledgeHub;
