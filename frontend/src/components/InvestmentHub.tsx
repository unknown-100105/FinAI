import { useMemo, useState } from "react";
import { BadgeIndianRupee, Banknote, Bitcoin, Calculator, Coins, Landmark, Percent, PiggyBank, ShieldCheck } from "lucide-react";
import "./PlatformModules.css";

const products = [
  ["mf", "Mutual Funds", "Fund categories and SIP planning.", PiggyBank],
  ["sip", "SIP", "Illustrative recurring-investment projection.", Calculator],
  ["bonds", "Bonds", "Coupon, maturity, yield and credit concepts.", Landmark],
  ["fd", "Fixed Deposits", "Illustrative maturity projection.", Banknote],
  ["post", "Post Office", "PPF, NSC, SCSS, MIS and related schemes.", BadgeIndianRupee],
  ["money", "Money Market", "T-bills, commercial paper and short-term instruments.", Coins],
  ["crypto", "Crypto", "Crypto assets alongside traditional markets.", Bitcoin],
  ["gold", "Gold", "Gold exposure and asset-class context.", ShieldCheck],
] as const;

function money(value: number) {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(value);
}

export function InvestmentHub() {
  const [active, setActive] = useState("sip");
  const [monthly, setMonthly] = useState("5000");
  const [rate, setRate] = useState("12");
  const [years, setYears] = useState("10");
  const [principal, setPrincipal] = useState("100000");
  const [fdRate, setFdRate] = useState("7");
  const [fdYears, setFdYears] = useState("5");

  const sip = useMemo(() => {
    const p = Number(monthly);
    const r = Number(rate) / 100 / 12;
    const n = Number(years) * 12;
    if (!Number.isFinite(p) || p <= 0 || !Number.isFinite(r) || !Number.isFinite(n) || n <= 0) return null;
    return r === 0 ? p * n : p * (((1 + r) ** n - 1) / r) * (1 + r);
  }, [monthly, rate, years]);

  const fd = useMemo(() => {
    const p = Number(principal);
    const r = Number(fdRate) / 100;
    const n = Number(fdYears);
    if (![p, r, n].every(Number.isFinite) || p <= 0 || n <= 0) return null;
    return p * (1 + r) ** n;
  }, [principal, fdRate, fdYears]);

  const selected = products.find((product) => product[0] === active);

  return (
    <section className="module-page">
      <div className="module-hero">
        <div>
          <div className="module-kicker"><PiggyBank size={14} /> Investment center</div>
          <h1>Money-market to crypto, in one view.</h1>
          <p>Product information and projections stay separate from current issuer rates or regulatory facts.</p>
        </div>
        <div className="module-orb"><Percent size={23} /></div>
      </div>

      <div className="product-grid">
        {products.map(([id, title, body, Icon]) => (
          <button type="button" key={id} className={active === id ? "product-card active" : "product-card"} onClick={() => setActive(id)}>
            <div className="product-icon"><Icon size={18} /></div>
            <strong>{title}</strong>
            <span>{body}</span>
          </button>
        ))}
      </div>

      <div className="calculator-panel">
        <div className="module-panel-head">
          <div>
            <div className="module-kicker"><Calculator size={13} /> Scenario workspace</div>
            <h2>{active === "sip" ? "SIP corpus" : active === "fd" ? "Fixed deposit maturity" : selected?.[1]}</h2>
          </div>
          <span className="source-chip"><ShieldCheck size={13} /> Assumptions visible</span>
        </div>

        {active === "sip" && (
          <div className="calc-grid">
            <label>Monthly investment<input type="number" value={monthly} onChange={(e) => setMonthly(e.target.value)} /></label>
            <label>Expected annual return %<input type="number" value={rate} onChange={(e) => setRate(e.target.value)} /></label>
            <label>Tenure (years)<input type="number" value={years} onChange={(e) => setYears(e.target.value)} /></label>
            <div className="calc-result"><span>Illustrative future value</span><strong>{sip ? money(sip) : "—"}</strong><small>Projection, not a guaranteed return.</small></div>
          </div>
        )}

        {active === "fd" && (
          <div className="calc-grid">
            <label>Principal<input type="number" value={principal} onChange={(e) => setPrincipal(e.target.value)} /></label>
            <label>Annual rate %<input type="number" value={fdRate} onChange={(e) => setFdRate(e.target.value)} /></label>
            <label>Tenure (years)<input type="number" value={fdYears} onChange={(e) => setFdYears(e.target.value)} /></label>
            <div className="calc-result"><span>Illustrative maturity</span><strong>{fd ? money(fd) : "—"}</strong><small>Issuer compounding may differ.</small></div>
          </div>
        )}

        {!["sip", "fd"].includes(active) && (
          <div className="product-detail">
            <div className="detail-icon"><ShieldCheck size={18} /></div>
            <div><strong>{selected?.[1]}</strong><p>{selected?.[2]} This module is structured for current authoritative product data, comparison criteria, eligibility and tax notes as those source sets are added.</p></div>
          </div>
        )}
      </div>
    </section>
  );
}

export default InvestmentHub;
