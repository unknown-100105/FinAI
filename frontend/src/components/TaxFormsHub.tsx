import { useEffect, useMemo, useState } from "react";
import { BadgeIndianRupee, CheckCircle2, ExternalLink, FileCheck2, FileText, Search, ShieldCheck } from "lucide-react";
import { calculateCapitalGainWorksheet, getComplianceCatalog, type ComplianceItem } from "../api/compliance";
import "./PlatformModules.css";

const categories = ["All", "Income Tax", "TDS", "Tax Information", "Income Tax Relief", "Foreign Tax Credit", "GST", "GST Composition"];

function money(value: unknown) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "—";
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(number);
}

export function TaxFormsHub() {
  const [category, setCategory] = useState("All");
  const [query, setQuery] = useState("");
  const [items, setItems] = useState<ComplianceItem[]>([]);
  const [meta, setMeta] = useState<Record<string, string>>({});
  const [selectedId, setSelectedId] = useState("itr1");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [buy, setBuy] = useState("0");
  const [sell, setSell] = useState("0");
  const [costs, setCosts] = useState("0");
  const [improvement, setImprovement] = useState("0");
  const [gain, setGain] = useState<number | null>(null);
  const [calcBusy, setCalcBusy] = useState(false);

  useEffect(() => {
    void getComplianceCatalog(category === "All" ? undefined : category)
      .then((data) => { setItems(data.items); setMeta(data.meta); })
      .catch((requestError) => setError(requestError instanceof Error ? requestError.message : "Compliance catalogue unavailable."))
      .finally(() => setLoading(false));
  }, [category]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return items;
    return items.filter((item) =>
      [item.name, item.item_id, item.category, item.purpose, item.period].join(" ").toLowerCase().includes(q),
    );
  }, [items, query]);

  const selected = filtered.find((item) => item.item_id === selectedId) ?? filtered[0] ?? items.find((item) => item.item_id === selectedId) ?? items[0];

  const calculateGain = async () => {
    setCalcBusy(true);
    setError("");
    try {
      const result = await calculateCapitalGainWorksheet({
        buy_value: Number(buy),
        sell_value: Number(sell),
        transfer_costs: Number(costs),
        improvement_cost: Number(improvement),
      });
      setGain(Number(result.result.computed_gain_before_tax));
    } catch (requestError) {
      setGain(null);
      setError(requestError instanceof Error ? requestError.message : "Capital-gain worksheet failed.");
    } finally {
      setCalcBusy(false);
    }
  };

  return (
    <section className="module-page">
      <div className="module-hero">
        <div>
          <div className="module-kicker"><FileCheck2 size={14} /> Tax & compliance intelligence</div>
          <h1>Forms, tax records, workflows — connected.</h1>
          <p>Navigate the current Indian tax/compliance landscape, understand what each form does, build a filing checklist, and calculate a pre-tax capital-gain worksheet.</p>
        </div>
        <div className="module-orb"><BadgeIndianRupee size={23} /></div>
      </div>

      {error && <div className="module-error">{error}</div>}
      {meta.tax_year_transition && (
        <div className="platform-banner">
          <ShieldCheck size={15} />
          <div><strong>2026 tax-law transition</strong><span>{meta.tax_year_transition}</span></div>
        </div>
      )}


      <div className="compliance-toolbar">
        <div className="compliance-search"><Search size={15} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search ITR, TDS, AIS, GST, capital gains…" /></div>
        <div className="compliance-categories">
          {categories.map((item) => (
            <button type="button" key={item} className={category === item ? "active" : ""} onClick={() => { if (category !== item) setLoading(true); setCategory(item); }}>{item}</button>
          ))}
        </div>
      </div>

      <div className="compliance-layout">
        <section className="workspace-panel compliance-list-panel">
          <div className="module-panel-head">
            <div><div className="module-kicker"><FileText size={13} /> Form navigator</div><h2>{filtered.length} reference items</h2></div>
            <span className="source-chip"><ShieldCheck size={13} /> Official-source links</span>
          </div>
          {loading ? <div className="module-empty">Loading compliance catalogue…</div> :
            filtered.length ? filtered.map((item) => (
              <button type="button" key={item.item_id} className={selected?.item_id === item.item_id ? "compliance-row active" : "compliance-row"} onClick={() => setSelectedId(item.item_id)}>
                <div><strong>{item.name}</strong><span>{item.category} · {item.period}</span></div>
                <small>{item.purpose}</small>
              </button>
            )) : <div className="module-empty">No form matched the search.</div>}
        </section>

        <section className="workspace-panel compliance-detail">
          {selected ? (
            <>
              <div className="module-panel-head">
                <div><div className="module-kicker">{selected.category}</div><h2>{selected.name}</h2></div>
                <a className="source-link" href={selected.official_url} target="_blank" rel="noreferrer">Official source <ExternalLink size={12} /></a>
              </div>
              <div className="compliance-facts">
                <div><span>Period</span><strong>{selected.period}</strong></div>
                <div><span>Who uses it</span><strong>{selected.who_uses_it}</strong></div>
              </div>
              <p className="compliance-purpose">{selected.purpose}</p>

              <div className="detail-section">
                <div className="detail-section-title">Key inputs</div>
                <div className="criteria-list">{selected.key_inputs.map((item) => <span key={item}><CheckCircle2 size={11} /> {item}</span>)}</div>
              </div>

              <div className="detail-section">
                <div className="detail-section-title">Execution workflow</div>
                <div className="workflow-list">{selected.workflow.map((step, index) => <div key={step}><b>{String(index + 1).padStart(2, "0")}</b><span>{step}</span></div>)}</div>
              </div>

              <div className="data-note"><strong>Source note:</strong> {selected.status_note}</div>
            </>
          ) : <div className="module-empty">Select a compliance item.</div>}
        </section>
      </div>

      <section className="workspace-panel calculator-workspace">
        <div className="module-panel-head">
          <div><div className="module-kicker"><BadgeIndianRupee size={13} /> Investment-tax worksheet</div><h2>Capital-gain worksheet</h2></div>
          <span className="source-chip">Pre-tax calculation</span>
        </div>
        <div className="advanced-calc-grid four">
          <label>Purchase value<input type="number" value={buy} onChange={(e) => setBuy(e.target.value)} /></label>
          <label>Sale value<input type="number" value={sell} onChange={(e) => setSell(e.target.value)} /></label>
          <label>Transfer costs<input type="number" value={costs} onChange={(e) => setCosts(e.target.value)} /></label>
          <label>Improvement cost<input type="number" value={improvement} onChange={(e) => setImprovement(e.target.value)} /></label>
        </div>
        <button type="button" className="primary-module-button" onClick={() => void calculateGain()} disabled={calcBusy}>{calcBusy ? "Calculating…" : "Calculate gain"}</button>
        {gain !== null && <div className="results-grid compact"><div><span>Computed gain before tax</span><strong>{money(gain)}</strong></div></div>}
        <p className="data-note">This worksheet calculates a simplified gain from the values entered. It does not determine the final tax liability, holding-period classification, indexation treatment, exemptions, surcharge, cess or set-off without the applicable law and transaction facts.</p>
      </section>
    </section>
  );
}

export default TaxFormsHub;
