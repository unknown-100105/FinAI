import { useEffect, useMemo, useState } from "react";
import { BadgeIndianRupee, Banknote, BarChart3, Calculator, CheckCircle2, Landmark, Percent, PiggyBank, ShieldCheck, TrendingUp } from "lucide-react";
import {
  getInvestmentCatalog,
  priceBond,
  projectFd,
  projectSip,
  projectSmallSavings,
  type InvestmentProduct,
  type MutualFundCategory,
} from "../api/investments";
import "./PlatformModules.css";

type Mode = "funds" | "small" | "sip" | "fd" | "bonds";

function money(value: unknown) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "—";
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(number);
}

function percent(value: unknown) {
  const number = Number(value);
  return Number.isFinite(number) ? `${number.toFixed(2)}%` : "—";
}

const modeCards: { id: Mode; title: string; body: string }[] = [
  { id: "funds", title: "Mutual Fund Explorer", body: "Current SEBI group structure with selection criteria." },
  { id: "small", title: "Post Office Rates", body: "Current Q3 FY 2026-27 notified small-savings rates." },
  { id: "sip", title: "SIP Planner", body: "Step-up, inflation and target-corpus planning." },
  { id: "fd", title: "FD Calculator", body: "Compounding and interest projection from your assumptions." },
  { id: "bonds", title: "Bond Analytics", body: "Estimate price from coupon, yield and maturity." },
];

export function InvestmentHub() {
  const [mode, setMode] = useState<Mode>("funds");
  const [products, setProducts] = useState<InvestmentProduct[]>([]);
  const [fundCategories, setFundCategories] = useState<MutualFundCategory[]>([]);
  const [meta, setMeta] = useState<{ rate_period: string; rate_source: string; rate_source_url: string; today: string; note: string } | null>(null);
  const [selectedProduct, setSelectedProduct] = useState("ppf");
  const [principal, setPrincipal] = useState("100000");
  const [monthly, setMonthly] = useState("5000");
  const [returnRate, setReturnRate] = useState("12");
  const [years, setYears] = useState("10");
  const [stepUp, setStepUp] = useState("10");
  const [inflation, setInflation] = useState("6");
  const [target, setTarget] = useState("10000000");
  const [fdRate, setFdRate] = useState("7");
  const [bondCoupon, setBondCoupon] = useState("7");
  const [bondYield, setBondYield] = useState("7.5");
  const [bondYears, setBondYears] = useState("5");
  const [result, setResult] = useState<Record<string, any> | null>(null);
  const [loading, setLoading] = useState(true);
  const [calculationLoading, setCalculationLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    void getInvestmentCatalog()
      .then((data) => {
        setProducts(data.small_savings);
        setFundCategories(data.mutual_fund_categories);
        setMeta(data.meta);
      })
      .catch((requestError) => setError(requestError instanceof Error ? requestError.message : "Investment catalog unavailable."))
      .finally(() => setLoading(false));
  }, []);

  const selected = useMemo(() => products.find((item) => item.product_id === selectedProduct) ?? products[0], [products, selectedProduct]);

  const calculate = async () => {
    setCalculationLoading(true);
    setError("");
    try {
      if (mode === "sip") {
        const data = await projectSip({
          monthly_investment: Number(monthly),
          annual_return_percent: Number(returnRate),
          years: Number(years),
          annual_step_up_percent: Number(stepUp),
          annual_inflation_percent: Number(inflation),
          target_corpus: Number(target),
        });
        setResult(data.result);
      } else if (mode === "fd") {
        const data = await projectFd({
          principal: Number(principal),
          annual_rate_percent: Number(fdRate),
          years: Number(years),
          compounding_per_year: 4,
        });
        setResult(data.result);
      } else if (mode === "bonds") {
        const data = await priceBond({
          face_value: Number(principal),
          coupon_rate_percent: Number(bondCoupon),
          yield_percent: Number(bondYield),
          years_to_maturity: Number(bondYears),
          coupon_frequency: 2,
        });
        setResult(data.result);
      } else if (mode === "small" && selected) {
        const data = await projectSmallSavings({
          product_id: selected.product_id,
          principal: Number(principal),
        });
        setResult(data.result);
      }
    } catch (requestError) {
      setResult(null);
      setError(requestError instanceof Error ? requestError.message : "Calculation failed.");
    } finally {
      setCalculationLoading(false);
    }
  };

  return (
    <section className="module-page">
      <div className="module-hero">
        <div>
          <div className="module-kicker"><PiggyBank size={14} /> Investment center</div>
          <h1>Explore, calculate, compare.</h1>
          <p>Financial products are no longer placeholder cards: the module loads structured data, current small-savings rates, source metadata and deterministic calculators.</p>
        </div>
        <div className="module-orb"><Percent size={23} /></div>
      </div>

      {error && <div className="module-error">{error}</div>}

      <div className="product-grid">
        {modeCards.map((card) => (
          <button key={card.id} type="button" className={mode === card.id ? "product-card active" : "product-card"} onClick={() => { setMode(card.id); setResult(null); }}>
            <div className="product-icon"><Calculator size={17} /></div>
            <strong>{card.title}</strong>
            <span>{card.body}</span>
          </button>
        ))}
      </div>

      {mode === "funds" && (
        <div className="investment-workspace">
          <div className="workspace-panel">
            <div className="module-panel-head"><div><div className="module-kicker"><BarChart3 size={13} /> Current structure</div><h2>Mutual fund groups</h2></div><a className="source-link" href="https://www.sebi.gov.in/legal/circulars/feb-2026/categorization-and-rationalization-of-mutual-fund-schemes_99983.html" target="_blank" rel="noreferrer">SEBI circular ↗</a></div>
            <div className="fund-category-grid">
              {fundCategories.map((category) => (
                <article className="fund-category-card" key={category.category_id}>
                  <div className="fund-category-top"><strong>{category.name}</strong><span>{category.group}</span></div>
                  <p>{category.description}</p>
                  <div className="criteria-list">
                    {category.what_to_check.map((item) => <span key={item}><CheckCircle2 size={11} /> {item}</span>)}
                  </div>
                </article>
              ))}
            </div>
          </div>
          <div className="workspace-panel fund-execution">
            <div className="module-kicker"><TrendingUp size={13} /> How FinAI executes</div>
            <h2>Fund selection is a process, not a hardcoded “best fund” list.</h2>
            <p>Use the category, then inspect a specific scheme's current factsheet, NAV, portfolio, costs, risk disclosures and performance period. This screen supplies the classification layer; live scheme-level data needs a current fund-data provider.</p>
            <div className="execution-steps">
              <span>01 · Category</span><span>02 · Scheme facts</span><span>03 · Compare</span><span>04 · Verify source</span>
            </div>
          </div>
        </div>
      )}

      {mode === "small" && (
        <div className="investment-workspace">
          <div className="workspace-panel">
            <div className="module-panel-head">
              <div><div className="module-kicker"><BadgeIndianRupee size={13} /> Government rate set</div><h2>Small-savings catalogue</h2></div>
              {meta && <a className="source-link" href={meta.rate_source_url} target="_blank" rel="noreferrer">Official source ↗</a>}
            </div>
            <div className="rate-table-wrap">
              <table className="rate-table">
                <thead><tr><th>Product</th><th>Rate</th><th>Tenure</th><th>Effective</th></tr></thead>
                <tbody>
                  {products.map((product) => (
                    <tr key={product.product_id} className={selected?.product_id === product.product_id ? "selected" : ""} onClick={() => { setSelectedProduct(product.product_id); setResult(null); }}>
                      <td><strong>{product.name}</strong><small>{product.payout}</small></td>
                      <td>{product.rate_percent == null ? "—" : percent(product.rate_percent)}</td>
                      <td>{product.tenure}</td>
                      <td>{product.effective_from ? `${product.effective_from} → ${product.effective_to}` : "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          <div className="workspace-panel">
            <div className="module-panel-head"><div><div className="module-kicker"><Calculator size={13} /> Scheme calculator</div><h2>{selected?.name || "Select a product"}</h2></div><span className="source-chip"><ShieldCheck size={13} /> Rate-linked</span></div>
            {selected && (
              <>
                <div className="product-fact-grid">
                  <div><span>Rate</span><strong>{percent(selected.rate_percent)}</strong></div>
                  <div><span>Tenure</span><strong>{selected.tenure}</strong></div>
                  <div><span>Eligibility</span><strong>{selected.eligibility}</strong></div>
                  <div><span>Liquidity</span><strong>{selected.liquidity}</strong></div>
                </div>
                <label className="single-field-label">Principal<input type="number" value={principal} onChange={(e) => setPrincipal(e.target.value)} /></label>
                <button className="primary-module-button" type="button" onClick={() => void calculate()} disabled={calculationLoading}>{calculationLoading ? "Calculating…" : "Calculate projection"}</button>
                {result && <div className="result-panel"><span>Illustrative result</span><strong>{money(result.illustrative_value)}</strong><small>{String(result.method)}</small></div>}
                <p className="data-note">{selected.tax_note} {meta?.note}</p>
              </>
            )}
          </div>
        </div>
      )}

      {mode === "sip" && (
        <div className="workspace-panel calculator-workspace">
          <div className="module-panel-head"><div><div className="module-kicker"><Calculator size={13} /> Goal planning</div><h2>SIP planner</h2></div><span className="source-chip">Assumptions explicit</span></div>
          <div className="advanced-calc-grid">
            <label>Monthly investment<input type="number" value={monthly} onChange={(e) => setMonthly(e.target.value)} /></label>
            <label>Expected annual return %<input type="number" value={returnRate} onChange={(e) => setReturnRate(e.target.value)} /></label>
            <label>Tenure (years)<input type="number" value={years} onChange={(e) => setYears(e.target.value)} /></label>
            <label>Annual step-up %<input type="number" value={stepUp} onChange={(e) => setStepUp(e.target.value)} /></label>
            <label>Inflation %<input type="number" value={inflation} onChange={(e) => setInflation(e.target.value)} /></label>
            <label>Target corpus<input type="number" value={target} onChange={(e) => setTarget(e.target.value)} /></label>
          </div>
          <button className="primary-module-button" type="button" onClick={() => void calculate()} disabled={calculationLoading}>{calculationLoading ? "Planning…" : "Run SIP plan"}</button>
          {result && <div className="results-grid">
            <div><span>Total invested</span><strong>{money(result.total_invested)}</strong></div>
            <div><span>Projected value</span><strong>{money(result.projected_value)}</strong></div>
            <div><span>Projected gain</span><strong>{money(result.projected_gain)}</strong></div>
            <div><span>Today's purchasing-power value</span><strong>{money(result.inflation_adjusted_value_today)}</strong></div>
            <div><span>Required starting SIP for target</span><strong>{money(result.required_starting_monthly_investment)}</strong></div>
          </div>}
          <p className="data-note">The return is a planning assumption, not a guaranteed mutual-fund return. The engine simulates monthly contributions and annual step-up.</p>
        </div>
      )}

      {mode === "fd" && (
        <div className="workspace-panel calculator-workspace">
          <div className="module-panel-head"><div><div className="module-kicker"><Banknote size={13} /> Deposit math</div><h2>Fixed deposit calculator</h2></div><span className="source-chip">User-supplied rate</span></div>
          <div className="advanced-calc-grid three">
            <label>Principal<input type="number" value={principal} onChange={(e) => setPrincipal(e.target.value)} /></label>
            <label>Annual rate %<input type="number" value={fdRate} onChange={(e) => setFdRate(e.target.value)} /></label>
            <label>Tenure (years)<input type="number" value={years} onChange={(e) => setYears(e.target.value)} /></label>
          </div>
          <button className="primary-module-button" type="button" onClick={() => void calculate()} disabled={calculationLoading}>{calculationLoading ? "Calculating…" : "Calculate maturity"}</button>
          {result && <div className="results-grid compact"><div><span>Maturity value</span><strong>{money(result.maturity_value)}</strong></div><div><span>Interest earned</span><strong>{money(result.interest_earned)}</strong></div><div><span>Compounding</span><strong>{String(result.compounding_per_year)}× / year</strong></div></div>}
          <p className="data-note">Actual bank FD rates, senior-citizen rates, TDS and premature-closure terms vary by institution and date. Enter the bank's current rate before using the projection.</p>
        </div>
      )}

      {mode === "bonds" && (
        <div className="workspace-panel calculator-workspace">
          <div className="module-panel-head"><div><div className="module-kicker"><Landmark size={13} /> Fixed-income analytics</div><h2>Bond price from yield</h2></div><span className="source-chip">Deterministic model</span></div>
          <div className="advanced-calc-grid four">
            <label>Face value<input type="number" value={principal} onChange={(e) => setPrincipal(e.target.value)} /></label>
            <label>Coupon %<input type="number" value={bondCoupon} onChange={(e) => setBondCoupon(e.target.value)} /></label>
            <label>Yield %<input type="number" value={bondYield} onChange={(e) => setBondYield(e.target.value)} /></label>
            <label>Years to maturity<input type="number" value={bondYears} onChange={(e) => setBondYears(e.target.value)} /></label>
          </div>
          <button className="primary-module-button" type="button" onClick={() => void calculate()} disabled={calculationLoading}>{calculationLoading ? "Pricing…" : "Price bond"}</button>
          {result && <div className="results-grid compact"><div><span>Estimated price</span><strong>{money(result.estimated_clean_price)}</strong></div><div><span>Annual coupon</span><strong>{money(result.annual_coupon)}</strong></div><div><span>Premium / discount</span><strong>{percent(Number(result.premium_discount_percent) / 100)}</strong></div></div>}
          <p className="data-note">This is a present-value estimate. Market price also depends on liquidity, accrued interest, credit risk, embedded options and the specific security terms.</p>
        </div>
      )}
    </section>
  );
}

export default InvestmentHub;
