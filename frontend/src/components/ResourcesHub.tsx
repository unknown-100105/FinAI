import { useEffect, useMemo, useState } from "react";
import { BookOpen, ExternalLink, FileCheck2, FileText, Landmark, Save, Search, ShieldCheck } from "lucide-react";
import { getOfficialResources, type OfficialResource } from "../api/resources";
import "./PlatformModules.css";

const tabs = ["All", "Government Schemes", "Investment Avenues", "Tax & Forms", "Study Material"];

function titleForField(field: string) {
  return field.replaceAll("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export function ResourcesHub({ defaultCategory = "All" }: { defaultCategory?: string }) {
  const [category, setCategory] = useState(defaultCategory);
  const [query, setQuery] = useState("");
  const [items, setItems] = useState<OfficialResource[]>([]);
  const [selectedId, setSelectedId] = useState("ppf");
  const [values, setValues] = useState<Record<string, string>>({});
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    void getOfficialResources(category === "All" ? undefined : category)
      .then((data) => setItems(data.items))
      .catch((requestError) => setError(requestError instanceof Error ? requestError.message : "Official resource catalogue unavailable."));
  }, [category]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return q ? items.filter((item) => [item.name,item.category,item.subcategory,item.summary].join(" ").toLowerCase().includes(q)) : items;
  }, [items, query]);

  const selected = filtered.find((item) => item.resource_id === selectedId) ?? items.find((item) => item.resource_id === selectedId) ?? filtered[0];

  useEffect(() => {
    if (!selected) return;
    const raw = localStorage.getItem("finai-form-" + selected.resource_id);
    setValues(raw ? JSON.parse(raw) : Object.fromEntries(selected.form_fields.map((field) => [field, ""])));
    setSaved(false);
  }, [selected?.resource_id]);

  const saveDraft = () => {
    if (!selected) return;
    localStorage.setItem("finai-form-" + selected.resource_id, JSON.stringify(values));
    setSaved(true);
  };

  const exportDraft = () => {
    if (!selected) return;
    const payload = JSON.stringify({ resource: selected.name, authority: selected.authority, fields: values }, null, 2);
    const blob = new Blob([payload], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = selected.resource_id + "-draft.json";
    anchor.click();
    URL.revokeObjectURL(url);
  };

  return (
    <section className="module-page">
      <div className="module-hero">
        <div>
          <div className="module-kicker"><Landmark size={14} /> Official resources + universal form workspace</div>
          <h1>Schemes, investments, tax forms and study material — with a form draft for every record.</h1>
          <p>Every resource carries an authority, status, source date, official link and form link where available. The filler creates a draft; it does not submit to a government portal.</p>
        </div>
        <div className="module-orb"><FileCheck2 size={23} /></div>
      </div>

      {error && <div className="module-error">{error}</div>}

      <div className="compliance-toolbar">
        <div className="compliance-search"><Search size={15} /><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search PPF, NPS, ETF, ITR-2, Form 10-IEA, GST…" /></div>
        <div className="compliance-categories">{tabs.map((item) => <button key={item} type="button" className={category === item ? "active" : ""} onClick={() => setCategory(item)}>{item}</button>)}</div>
      </div>

      <div className="resources-layout">
        <section className="workspace-panel resource-list-panel">
          <div className="module-panel-head">
            <div><div className="module-kicker"><BookOpen size={13} /> Source directory</div><h2>{filtered.length} resources</h2></div>
            <span className="source-chip"><ShieldCheck size={13} /> Official-source first</span>
          </div>
          <div className="resource-list">
            {filtered.map((item) => (
              <button type="button" key={item.resource_id} className={selected?.resource_id === item.resource_id ? "resource-row active" : "resource-row"} onClick={() => setSelectedId(item.resource_id)}>
                <div><strong>{item.name}</strong><span>{item.category} · {item.subcategory}</span></div>
                <em>{item.current_status}</em>
              </button>
            ))}
          </div>
        </section>

        <section className="workspace-panel resource-detail">
          {selected ? (
            <>
              <div className="module-panel-head">
                <div><div className="module-kicker">{selected.category}</div><h2>{selected.name}</h2></div>
                <a className="source-link" title="Current official link" href={selected.official_url} target="_blank" rel="noreferrer">Official source <ExternalLink size={12} /></a>
              </div>
              <p className="resource-summary">{selected.summary}</p>
              <div className="resource-facts">
                <div><span>Authority</span><strong>{selected.authority}</strong></div>
                <div><span>Status / period</span><strong>{selected.current_status}</strong></div>
                <div><span>Source date</span><strong>{selected.source_date}</strong></div>
              </div>
              <div className="resource-actions">
                {selected.form_url && <a className="primary-module-button link-button" href={selected.form_url} target="_blank" rel="noreferrer"><FileText size={13} /> Open official form/source</a>}
                <button type="button" className="secondary-module-button" onClick={saveDraft}><Save size={13} /> {saved ? "Draft saved" : "Save draft"}</button>
                <button type="button" className="secondary-module-button" onClick={exportDraft}>Export JSON</button>
              </div>
              <div className="detail-section">
                <div className="detail-section-title">Form filler</div>
                <div className="advanced-calc-grid two">
                  {selected.form_fields.map((field) => (
                    <label key={field}>{titleForField(field)}
                      <input value={values[field] ?? ""} onChange={(e) => setValues((current) => ({ ...current, [field]: e.target.value }))} placeholder={"Enter " + titleForField(field).toLowerCase()} />
                    </label>
                  ))}
                </div>
              </div>
              <div className="data-note"><strong>Notes:</strong> {selected.notes}</div>
            </>
          ) : <div className="module-empty">No resource selected.</div>}
        </section>
      </div>
    </section>
  );
}

export default ResourcesHub;
