import { useEffect, useMemo, useState } from "react";
import { ExternalLink, FilePenLine, Search, ShieldCheck, Save, Download } from "lucide-react";
import { getOfficialResources, type OfficialResource } from "../api/resources";
import "./PlatformModules.css";

function labelize(field: string) {
  return field.replaceAll("_", " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

export function SchemesFormsHub() {
  const [category, setCategory] = useState("All");
  const [query, setQuery] = useState("");
  const [resources, setResources] = useState<OfficialResource[]>([]);
  const [selectedId, setSelectedId] = useState("ppf");
  const [values, setValues] = useState<Record<string, string>>({});
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    void getOfficialResources(category === "All" ? undefined : category)
      .then((data) => setResources(data.items))
      .catch((requestError) => setError(requestError instanceof Error ? requestError.message : "Unable to load official resources."));
  }, [category]);

  const filtered = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) return resources;
    return resources.filter((item) =>
      [item.name, item.category, item.authority, item.description].join(" ").toLowerCase().includes(normalized),
    );
  }, [resources, query]);

  const selected = filtered.find((item) => item.resource_id === selectedId) ?? resources.find((item) => item.resource_id === selectedId) ?? filtered[0];
  
  useEffect(() => {
    if (!selected) return;
    const existing = window.localStorage.getItem("finai.form." + selected.resource_id);
    if (existing) {
      try { setValues(JSON.parse(existing) as Record<string, string>); } catch { setValues({}); }
    } else {
      setValues(Object.fromEntries(selected.form_fields.map((field) => [field, ""])));
    }
    setSaved(false);
  }, [selected?.resource_id]);

  const saveDraft = () => {
    if (!selected) return;
    window.localStorage.setItem("finai.form." + selected.resource_id, JSON.stringify(values));
    setSaved(true);
  };

  const downloadDraft = () => {
    if (!selected) return;
    const lines = [
      selected.name,
      "Authority: " + selected.authority,
      "Official source: " + selected.official_url,
      "",
      ...selected.form_fields.map((field) => labelize(field) + ": " + (values[field] || "")),
    ];
    const blob = new Blob([lines.join("\n")], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "finai-" + selected.resource_id + "-draft.txt";
    link.click();
    URL.revokeObjectURL(url);
  };

  const categories = ["All", ...Array.from(new Set(resources.map((item) => item.category)))];

  return (
    <section className="module-page">
      <div className="module-hero">
        <div>
          <div className="module-kicker"><ShieldCheck size={14} /> Official schemes + forms workspace</div>
          <h1>Every resource gets a source. Every supported resource gets a fillable draft.</h1>
          <p>FinAI keeps official links visible, separates source facts from your personal draft, and never submits a form to a government portal automatically.</p>
        </div>
        <div className="module-orb"><FilePenLine size={23} /></div>
      </div>

      {error && <div className="module-error">{error}</div>}

      <div className="compliance-toolbar">
        <div className="compliance-search"><Search size={15} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search PPF, NPS, ITR-2, EPF, RBI Retail Direct, GSTR-1…" /></div>
        <div className="compliance-categories">
          {categories.map((item) => <button type="button" key={item} className={category === item ? "active" : ""} onClick={() => setCategory(item)}>{item}</button>)}
        </div>
      </div>

      <div className="compliance-layout resource-layout">
        <section className="workspace-panel compliance-list-panel">
          <div className="module-panel-head"><div><div className="module-kicker">Catalogue</div><h2>{filtered.length} resources</h2></div><span className="source-chip">Official-source mapped</span></div>
          {filtered.map((item) => (
            <button type="button" key={item.resource_id} className={selected?.resource_id === item.resource_id ? "compliance-row active" : "compliance-row"} onClick={() => setSelectedId(item.resource_id)}>
              <div><strong>{item.name}</strong><span>{item.category} · {item.authority}</span></div>
              <small>{item.description}</small>
            </button>
          ))}
        </section>

        <section className="workspace-panel compliance-detail">
          {selected ? (
            <>
              <div className="module-panel-head">
                <div><div className="module-kicker">{selected.category}</div><h2>{selected.name}</h2></div>
                <a className="source-link" href={selected.official_url} target="_blank" rel="noreferrer">Official source <ExternalLink size={12} /></a>
              </div>
              <div className="compliance-facts">
                <div><span>Authority</span><strong>{selected.authority}</strong></div>
                <div><span>Audience</span><strong>{selected.audience.join(", ")}</strong></div>
              </div>
              <p className="compliance-purpose">{selected.description}</p>
              <div className="data-note">{selected.current_source ? "Official source mapped. Verify current terms before a real transaction." : "Educational source. Verify current terms before a real transaction."}</div>
              

              <div className="detail-section">
                <div className="module-panel-head">
                  <div><div className="detail-section-title">FinAI form filler / preparation draft</div><span className="data-note">Local browser draft; not official submission.</span></div>
                  <div className="resource-form-actions">
                    <button type="button" onClick={saveDraft}><Save size={12}/>{saved ? "Saved" : "Save draft"}</button>
                    <button type="button" onClick={downloadDraft}><Download size={12}/>Export</button>
                  </div>
                </div>
                <div className="advanced-calc-grid two">
                  {selected.form_fields.map((field) => (
                    <label key={field}>{labelize(field)}<input value={values[field] ?? ""} onChange={(event) => setValues((current) => ({ ...current, [field]: event.target.value }))} /></label>
                  ))}
                </div>
              </div>
            </>
          ) : <div className="module-empty">No resource matched.</div>}
        </section>
      </div>
    </section>
  );
}

export default SchemesFormsHub;
