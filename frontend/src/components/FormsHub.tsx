import { useMemo, useState } from "react";
import { CheckCircle2, Download, FileText, RotateCcw, UserRound } from "lucide-react";
import "./PlatformModules.css";

const types = ["General KYC profile", "Investment account profile", "Bank service request", "Post Office service request"];

type Profile = {
  fullName: string;
  pan: string;
  address: string;
  city: string;
  state: string;
  pincode: string;
  phone: string;
  email: string;
};

const emptyProfile: Profile = { fullName: "", pan: "", address: "", city: "", state: "", pincode: "", phone: "", email: "" };

export function FormsHub() {
  const [formType, setFormType] = useState(types[0]);
  const [profile, setProfile] = useState<Profile>(() => {
    try {
      return JSON.parse(localStorage.getItem("finai.formProfile") || "null") || emptyProfile;
    } catch {
      return emptyProfile;
    }
  });

  const fields = useMemo(() => Object.entries(profile) as [keyof Profile, string][], [profile]);
  const complete = Object.values(profile).every((value) => value.trim());
  const validPan = !profile.pan || /^[A-Za-z]{5}[0-9]{4}[A-Za-z]$/.test(profile.pan);
  const validPincode = !profile.pincode || /^[0-9]{6}$/.test(profile.pincode);

  const update = (key: keyof Profile, value: string) => {
    const next = { ...profile, [key]: value };
    setProfile(next);
    localStorage.setItem("finai.formProfile", JSON.stringify(next));
  };

  const reset = () => {
    setProfile(emptyProfile);
    localStorage.removeItem("finai.formProfile");
  };

  const exportDraft = () => {
    const text = ["FinAI — " + formType, "", ...fields.map(([key, value]) => key + ": " + value)].join("\n");
    const url = URL.createObjectURL(new Blob([text], { type: "text/plain;charset=utf-8" }));
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "finai-form-draft.txt";
    anchor.click();
    URL.revokeObjectURL(url);
  };

  return (
    <section className="module-page">
      <div className="module-hero compact-hero">
        <div>
          <div className="module-kicker"><FileText size={14} /> Form assistant</div>
          <h1>Prepare once, review carefully, export a draft.</h1>
          <p>This creates a local, reviewable draft. It does not submit anything to an institution.</p>
        </div>
        <div className="module-orb"><UserRound size={23} /></div>
      </div>

      <div className="form-layout">
        <section className="form-panel">
          <div className="module-panel-head">
            <div><div className="module-kicker">Workflow</div><h2>Profile fields</h2></div>
            {complete && validPan && validPincode ? <span className="form-good"><CheckCircle2 size={13} /> Ready for review</span> : <span className="form-pending">Incomplete</span>}
          </div>

          <label className="form-select-label">Form type<select value={formType} onChange={(e) => setFormType(e.target.value)}>{types.map((type) => <option key={type}>{type}</option>)}</select></label>

          <div className="form-fields">
            {([
              ["fullName", "Full name"], ["pan", "PAN"], ["address", "Address"], ["city", "City"],
              ["state", "State"], ["pincode", "Pincode"], ["phone", "Phone"], ["email", "Email"],
            ] as const).map(([key, label]) => (
              <label key={key}>{label}<input value={profile[key]} onChange={(e) => update(key, e.target.value)} /></label>
            ))}
          </div>

          {!validPan && <div className="module-error">PAN format needs review.</div>}
          {!validPincode && <div className="module-error">Pincode must contain 6 digits.</div>}

          <div className="form-actions">
            <button type="button" onClick={reset}><RotateCcw size={13} /> Reset</button>
            <button type="button" onClick={exportDraft} disabled={!complete || !validPan || !validPincode}><Download size={13} /> Export draft</button>
          </div>
        </section>

        <aside className="form-preview">
          <div className="module-kicker">Preview</div>
          <h2>{formType}</h2>
          <div className="review-list">{fields.map(([key, value]) => <div key={key}><span>{key}</span><strong>{value || "Not provided"}</strong></div>)}</div>
        </aside>
      </div>
    </section>
  );
}

export default FormsHub;
