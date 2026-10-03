import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, BrainCircuit, Gauge, Network, Play, RotateCcw, ShieldAlert } from "lucide-react";
import { getCausalArchitecture, getCausalGraph, runCounterfactual, type CausalGraph, type CounterfactualResult } from "../api/causalRisk";
import "./CausalRiskLab.css";

type K = "rates" | "supply" | "oil" | "credit" | "usd";
type S = Record<K, number>;

const labels: Record<K, string> = {
  rates: "Policy rate",
  supply: "East Asia supply",
  oil: "Energy",
  credit: "Credit spreads",
  usd: "USD / INR",
};

const fallbackGraph: CausalGraph = {
  nodes: [
    { node_id: "rates", label: "Central-bank rates", kind: "macro" },
    { node_id: "usd", label: "USD / INR", kind: "macro" },
    { node_id: "oil", label: "Energy prices", kind: "commodity" },
    { node_id: "supply", label: "East Asia supply", kind: "supply_chain" },
    { node_id: "credit", label: "Credit spreads", kind: "funding" },
    { node_id: "liquidity", label: "Market liquidity", kind: "market" },
    { node_id: "equity", label: "Equity risk", kind: "market" },
    { node_id: "portfolio", label: "Portfolio drawdown", kind: "outcome" },
  ],
  edges: [
    { source: "rates", target: "credit", weight: 0.72 },
    { source: "rates", target: "equity", weight: 0.64 },
    { source: "usd", target: "oil", weight: 0.35 },
    { source: "oil", target: "credit", weight: 0.28 },
    { source: "supply", target: "liquidity", weight: 0.61 },
    { source: "credit", target: "liquidity", weight: 0.68 },
    { source: "credit", target: "equity", weight: 0.57 },
    { source: "liquidity", target: "equity", weight: 0.74 },
    { source: "equity", target: "portfolio", weight: 0.83 },
  ],
  engine: "fallback",
  semantics: "fallback graph",
  learned_components_status: {},
};

const positions: Record<string, [number, number]> = {
  rates: [14, 20],
  usd: [35, 10],
  oil: [60, 18],
  supply: [78, 34],
  credit: [30, 48],
  liquidity: [55, 50],
  equity: [76, 64],
  portfolio: [53, 82],
};

const portfolios = {
  balanced: { name: "Balanced India", equity: 55, debt: 30, gold: 10, cash: 5 },
  growth: { name: "Growth", equity: 75, debt: 10, gold: 10, cash: 5 },
  defensive: { name: "Defensive", equity: 25, debt: 55, gold: 15, cash: 5 },
};

const defaults: S = { rates: 75, supply: 60, oil: 35, credit: 40, usd: 15 };
const localCalc = (s: S, p: typeof portfolios.balanced) => {
  const l = -(s.rates * 0.18 + s.supply * 0.22 + s.credit * 0.24 + s.oil * 0.08 + s.usd * 0.07);
  const e = -(s.rates * 0.13 + s.supply * 0.17 + s.oil * 0.11 + s.credit * 0.21 + s.usd * 0.08) + l * 0.24;
  const d = -(s.rates * 0.05 + s.credit * 0.16) + s.oil * 0.02 - l * 0.008;
  const draw = (p.equity * e + p.debt * d) / 100;
  const risk = Math.min(100, Math.abs(l) * 0.34 + Math.abs(e) * 0.32 + Math.abs(d) * 0.18 + Math.abs(draw) * 0.16);
  return { l, e, d, draw, risk };
};
const pct = (x: number) => `${x > 0 ? "+" : ""}${x.toFixed(1)}%`;

export default function CausalRiskLab() {
  const [s, setS] = useState<S>(defaults);
  const [p, setP] = useState<keyof typeof portfolios>("balanced");
  const [graph, setGraph] = useState<CausalGraph>(fallbackGraph);
  const [architecture, setArchitecture] = useState<Record<string, unknown> | null>(null);
  const [result, setResult] = useState<CounterfactualResult | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const fallback = useMemo(() => localCalc(s, portfolios[p]), [s, p]);

  useEffect(() => {
    void Promise.all([getCausalGraph(), getCausalArchitecture()])
      .then(([nextGraph, nextArchitecture]) => {
        setGraph(nextGraph);
        setArchitecture(nextArchitecture);
      })
      .catch(() => setError("Causal API unavailable; using local research fallback."));
  }, []);

  const run = async () => {
    setRunning(true);
    setError("");
    try {
      const next = await runCounterfactual({
        shock: s,
        allocation: {
          equity: portfolios[p].equity,
          debt: portfolios[p].debt,
          gold: portfolios[p].gold,
          cash: portfolios[p].cash,
        },
        include_tail_scenarios: true,
      });
      setResult(next);
    } catch (requestError) {
      setResult(null);
      setError(requestError instanceof Error ? requestError.message : "Counterfactual run failed");
    } finally {
      setRunning(false);
    }
  };

  const reset = () => {
    setS(defaults);
    setResult(null);
  };

  const graphNodes = graph.nodes.filter((node) => positions[node.node_id]);
  const graphEdges = graph.edges.filter((edge) => positions[edge.source] && positions[edge.target]);

  const risk = result?.systemic_stress ?? fallback.risk;
  const liquidity = result?.channels.liquidity ?? fallback.l;
  const equity = result?.channels.equity ?? fallback.e;
  const debt = result?.channels.debt ?? fallback.d;
  const draw = result?.channels.portfolio ?? fallback.draw;
  const primaryPath = result?.explanation.primary_path ?? ["rates", "credit", "liquidity", "equity", "portfolio"];
  const tail = result?.tail_evaluation;
  const topTailScenarios = [...(tail?.scenarios ?? [])].sort((a, b) => b.systemic_stress - a.systemic_stress).slice(0, 5);

  return <section className="causal-page">
    <header className="causal-hero">
      <div>
        <div className="causal-kicker"><BrainCircuit size={14}/> FinAI Research · Causal intelligence</div>
        <h1>Counterfactual systemic-risk lab</h1>
        <p>Model why a shock propagates through macro conditions, supply chains, liquidity and portfolio exposures.</p>
      </div>
      <div className="causal-hero-metrics">
        <div><span>Graph</span><strong>{graphEdges.length} links</strong></div>
        <div><span>Engine</span><strong>SCM v0.2</strong></div>
        <div><span>Discovery</span><strong>{String(graph.learned_components_status.notears_linear ?? "research")}</strong></div>
      </div>
    </header>

    <div className="causal-command">
      <label>Portfolio<select value={p} onChange={(e) => setP(e.target.value as keyof typeof portfolios)}>{Object.entries(portfolios).map(([k, v]) => <option key={k} value={k}>{v.name}</option>)}</select></label>
      <button className="causal-run" onClick={() => void run()} disabled={running}><Play size={13}/>{running ? "Propagating…" : "Run counterfactual"}</button>
      <button className="causal-reset" onClick={reset}><RotateCcw size={13}/>Reset</button>
    </div>

    {error && <div className="module-error">{error}</div>}

    <div className="causal-main">
      <section className="causal-panel causal-graph-panel">
        <div className="causal-panel-head">
          <div><div className="causal-label">01 · Dynamic causal graph</div><h2>Systemic dependency map</h2></div>
          <span className="causal-badge"><Network size={12}/> Directed</span>
        </div>
        <div className="causal-graph">
          <svg viewBox="0 0 100 100" preserveAspectRatio="none">
            {graphEdges.map((edge) => {
              const a = positions[edge.source], b = positions[edge.target];
              return <line key={edge.source + edge.target} x1={a[0]} y1={a[1]} x2={b[0]} y2={b[1]}/>;
            })}
          </svg>
          {graphNodes.map((node) => {
            const [x, y] = positions[node.node_id];
            const intervention = (Object.keys(s) as string[]).includes(node.node_id);
            return <div key={node.node_id} className={intervention ? "causal-node intervention" : "causal-node"} style={{ left: `${x}%`, top: `${y}%` }}>
              <span>{node.kind === "outcome" ? "Outcome" : "Variable"}</span><strong>{node.label.replace("Central-bank ", "")}</strong>
            </div>;
          })}
        </div>
      </section>

      <aside className="causal-panel causal-controls">
        <div className="causal-label">02 · Do-operator</div>
        <h2>Intervention controls</h2>
        <p>Set hypothetical interventions. These are scenarios, not forecasts.</p>
        {(Object.keys(s) as K[]).map((key) => <label className="shock" key={key}>
          <span>{labels[key]} <b>{s[key]}%</b></span>
          <input type="range" min="-100" max="150" value={s[key]} onChange={(e) => setS((value) => ({ ...value, [key]: Number(e.target.value) }))}/>
        </label>)}
        <div className="formula"><code>P(Y | do(X=x))</code><small>Structural intervention on X</small></div>
        {architecture && <div className="formula"><code>{String(architecture.status ?? "architecture")}</code><small>TGAT research component</small></div>}
      </aside>
    </div>

    <div className="causal-results">
      <section className="causal-panel result-card">
        <div className="causal-label">03 · Systemic risk</div>
        <div className="risk-number"><Gauge size={17}/><strong>{risk.toFixed(0)}</strong><span>/100 stress</span></div>
        <div className="risk-bar"><i style={{ width: `${risk}%` }}/></div>
        <div className="metric-list">
          <div><span>Liquidity</span><b>{pct(liquidity)}</b></div>
          <div><span>Equity channel</span><b>{pct(equity)}</b></div>
          <div><span>Debt channel</span><b>{pct(debt)}</b></div>
        </div>
      </section>

      <section className="causal-panel result-card">
        <div className="causal-label">04 · Intrinsic explanation</div>
        <h2>Why the shock reaches the portfolio</h2>
        <ol>
          <li>Interventions are fixed with <code>do(X=x)</code> rather than merely appended as predictive features.</li>
          <li>Directed edge weights transmit the intervention through the structural graph.</li>
          <li>Liquidity and equity channels aggregate downstream effects.</li>
          <li>Portfolio allocation converts channel stress into a scenario drawdown.</li>
        </ol>
        <div className="explain"><ShieldAlert size={13}/> Structural path, not post-hoc SHAP importance.</div>
        <div className="causal-path"><span>Primary:</span>{primaryPath.map((node, index) => <span key={node}>{node}{index < primaryPath.length - 1 ? " → " : ""}</span>)}</div>
      </section>

      <section className="causal-panel result-card">
        <div className="causal-label">05 · Counterfactual portfolio</div>
        <h2>{portfolios[p].name}</h2>
        <div className="allocation">
          <div><span>Equity</span><i style={{ width: `${portfolios[p].equity}%` }}/><b>{portfolios[p].equity}%</b></div>
          <div><span>Debt</span><i style={{ width: `${portfolios[p].debt}%` }}/><b>{portfolios[p].debt}%</b></div>
          <div><span>Gold</span><i style={{ width: `${portfolios[p].gold}%` }}/><b>{portfolios[p].gold}%</b></div>
        </div>
        <div className="counterfactual"><span>Scenario change</span><strong>{pct(draw)}</strong></div>
        {result?.tail_scenarios && <div className="tail-mini"><span>Tail sampler</span><strong>{result.tail_scenarios.scenario_count} scenarios</strong><small>{result.tail_scenarios.gfnets_status}</small></div>}
      </section>
    </div>

    {tail && <section className="causal-panel tail-panel">
      <div className="tail-head">
        <div>
          <div className="causal-label">06 · Tail scenario evaluation</div>
          <h2>Stress distribution after SCM propagation</h2>
          <p>Each generated tail shock is evaluated through the same structural model used by the main counterfactual.</p>
        </div>
        <span className="tail-status">{tail.status}</span>
      </div>
      <div className="tail-summary">
        <div><span>Mean stress</span><strong>{tail.summary.mean_systemic_stress.toFixed(1)}</strong></div>
        <div><span>P90</span><strong>{tail.summary.systemic_stress_p90.toFixed(1)}</strong></div>
        <div><span>P95</span><strong>{tail.summary.systemic_stress_p95.toFixed(1)}</strong></div>
        <div><span>P99</span><strong>{tail.summary.systemic_stress_p99.toFixed(1)}</strong></div>
        <div><span>Max</span><strong>{tail.summary.max_systemic_stress.toFixed(1)}</strong></div>
      </div>
      <div className="tail-grid">
        <div className="tail-table">
          <div className="tail-row tail-row-head"><span>Scenario</span><span>Stress</span><span>Portfolio</span><span>Primary path</span></div>
          {topTailScenarios.map((scenario) => <div className="tail-row" key={scenario.scenario_id}>
            <span><b>{scenario.scenario_id}</b><small>tail score {scenario.tail_score.toFixed(2)}</small></span>
            <span><i className="tail-meter"><em style={{ width: `${Math.min(100, scenario.systemic_stress)}%` }}/></i><b>{scenario.systemic_stress.toFixed(1)}</b></span>
            <span>{pct(scenario.portfolio_impact)}</span>
            <span className="tail-path">{scenario.primary_path.join(" → ")}</span>
          </div>)}
        </div>
        <div className="tail-boundary">
          <div className="causal-label">Research status</div>
          <strong>{result?.tail_scenarios?.gfnets_status ?? "not available"}</strong>
          <p>The current tail generator is a reproducible Monte-Carlo baseline. GFlowNet is represented as an interface and has not been trained in this repository.</p>
          <div className="tail-quantiles">
            <span>Portfolio |P| P90 <b>{tail.summary.absolute_portfolio_impact_p90.toFixed(1)}%</b></span>
            <span>Portfolio |P| P95 <b>{tail.summary.absolute_portfolio_impact_p95.toFixed(1)}%</b></span>
            <span>Portfolio |P| P99 <b>{tail.summary.absolute_portfolio_impact_p99.toFixed(1)}%</b></span>
          </div>
        </div>
      </div>
    </section>}

    <footer className="causal-note">
      <AlertTriangle size={14}/>
      <span><b>Research boundary:</b> NOTEARS linear discovery and a lagged temporal baseline are implemented; TGAT is an architecture module, and GFlowNet tail generation is not trained yet. All scenario coefficients require empirical calibration before production use.</span>
    </footer>
  </section>;
}
