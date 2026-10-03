import { useMemo, useState } from "react";
import {
  Check,
  CircleAlert,
  Code2,
  Copy,
  Download,
  Gauge,
  KeyRound,
  Layers3,
  LockKeyhole,
  Play,
  ShieldCheck,
  Sparkles,
  TerminalSquare,
  WalletCards,
  Zap,
} from "lucide-react";
import "./PlatformModules.css";

type FeatureKey = "burnable" | "pausable" | "capped" | "permit" | "mintable";

const tokenLabTabs: Array<{ id: "design" | "code" | "security"; label: string; icon: typeof Layers3 }> = [\n  { id: "design", label: "Design studio", icon: Layers3 },\n  { id: "code", label: "Contract source", icon: Code2 },\n  { id: "security", label: "Security review", icon: ShieldCheck },\n];\n\nconst featureMeta: Array<{
  id: FeatureKey;
  label: string;
  description: string;
  icon: typeof Zap;
}> = [
  { id: "burnable", label: "Burnable", description: "Token holders can permanently burn tokens.", icon: Zap },
  { id: "pausable", label: "Pausable", description: "Owner can pause transfers during an incident.", icon: LockKeyhole },
  { id: "capped", label: "Supply cap", description: "Hard maximum supply enforced by the contract.", icon: Gauge },
  { id: "permit", label: "Permit", description: "EIP-2612 approvals without a separate approve transaction.", icon: KeyRound },
  { id: "mintable", label: "Controlled mint", description: "Owner can mint additional tokens after deployment.", icon: Sparkles },
];

const chainMeta = [
  { id: "ethereum", label: "Ethereum", fee: "High gas", badge: "L1" },
  { id: "polygon", label: "Polygon", fee: "Low gas", badge: "L2" },
  { id: "base", label: "Base", fee: "Low gas", badge: "L2" },
  { id: "arbitrum", label: "Arbitrum", fee: "Low gas", badge: "L2" },
  { id: "bsc", label: "BNB Chain", fee: "Low gas", badge: "L1" },
] as const;

function cleanIdentifier(value: string, fallback: string) {
  const cleaned = value.replace(/[^A-Za-z0-9]/g, "");
  if (!cleaned) return fallback;
  return /^[0-9]/.test(cleaned) ? `T${cleaned}` : cleaned;
}

function cleanSymbol(value: string) {
  return value.toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 12) || "FINAI";
}

function cleanInteger(value: string, fallback: string) {
  const cleaned = value.replace(/[^0-9]/g, "");
  return cleaned || fallback;
}

function buildSolidity(
  name: string,
  symbol: string,
  decimals: number,
  supply: string,
  cap: string,
  features: Record<FeatureKey, boolean>,
) {
  const imports = [
    'import "@openzeppelin/contracts/token/ERC20/ERC20.sol";',
    features.burnable && 'import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";',
    features.pausable && 'import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Pausable.sol";',
    features.capped && 'import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Capped.sol";',
    features.permit && 'import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Permit.sol";',
    (features.pausable || features.capped || features.mintable) && 'import "@openzeppelin/contracts/access/Ownable.sol";',
  ].filter(Boolean).join("\n");

  const parents = [
    "ERC20",
    features.burnable && "ERC20Burnable",
    features.pausable && "ERC20Pausable",
    features.capped && "ERC20Capped",
    features.permit && "ERC20Permit",
    (features.pausable || features.capped || features.mintable) && "Ownable",
  ].filter(Boolean).join(", ");

  const constructors = [
    `constructor() ERC20("${name}", "${symbol}")`,
    features.capped ? ` ERC20Capped(${cap} * 10 ** ${decimals})` : "",
    features.permit ? ` ERC20Permit("${name}")` : "",
    (features.pausable || features.capped || features.mintable) ? " Ownable(msg.sender)" : "",
    " {",
    `        _mint(msg.sender, ${supply} * 10 ** ${decimals});`,
    "    }",
  ].join("\n");

  const mintFunction = features.mintable
    ? `\n    function mint(address to, uint256 amount) external onlyOwner {\n        _mint(to, amount);\n    }\n`
    : "";

  const pauseFunctions = features.pausable
    ? `\n    function pause() external onlyOwner {\n        _pause();\n    }\n\n    function unpause() external onlyOwner {\n        _unpause();\n    }\n`
    : "";

  const updateOverride =
    features.pausable || features.capped
      ? `\n    function _update(address from, address to, uint256 value)\n        internal\n        override(ERC20${features.pausable ? ", ERC20Pausable" : ""}${features.capped ? ", ERC20Capped" : ""})\n    {\n        super._update(from, to, value);\n    }\n`
      : "";

  return `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

${imports}

contract ${cleanIdentifier(name, "FinAIToken")} is ${parents} {
${constructors}
${mintFunction}${pauseFunctions}${updateOverride}
}
`;
}

function featureChecks(features: Record<FeatureKey, boolean>, supply: string, cap: string) {
  const checks = [
    { label: "Fixed-point decimals bounded to 0–18", ok: true },
    { label: "Initial supply is a positive integer", ok: Number(supply) > 0 },
    { label: "Supply cap contains initial supply", ok: !features.capped || Number(cap) >= Number(supply) },
    { label: "No private keys or RPC credentials are generated", ok: true },
    { label: "No deployment transaction is executed", ok: true },
    { label: "OpenZeppelin extension imports are explicit", ok: true },
  ];
  return checks;
}

export function TokenGeneratorHub() {
  const [name, setName] = useState("FinAI Token");
  const [symbol, setSymbol] = useState("FINAI");
  const [supply, setSupply] = useState("1000000");
  const [cap, setCap] = useState("10000000");
  const [decimals, setDecimals] = useState("18");
  const [chain, setChain] = useState<(typeof chainMeta)[number]["id"]>("ethereum");
  const [activeTab, setActiveTab] = useState<"design" | "code" | "security">("design");
  const [copied, setCopied] = useState(false);
  const [features, setFeatures] = useState<Record<FeatureKey, boolean>>({
    burnable: true,
    pausable: false,
    capped: true,
    permit: true,
    mintable: false,
  });

  const safeName = cleanIdentifier(name, "FinAIToken");
  const safeSymbol = cleanSymbol(symbol);
  const safeSupply = cleanInteger(supply, "1000000");
  const safeCap = cleanInteger(cap, "10000000");
  const safeDecimals = Math.max(0, Math.min(18, Number(decimals) || 18));
  const selectedChain = chainMeta.find((item) => item.id === chain) ?? chainMeta[0];
  const checks = useMemo(
    () => featureChecks(features, safeSupply, safeCap),
    [features, safeSupply, safeCap],
  );
  const ready = checks.every((check) => check.ok);

  const code = useMemo(
    () => buildSolidity(safeName, safeSymbol, safeDecimals, safeSupply, safeCap, features),
    [safeName, safeSymbol, safeDecimals, safeSupply, safeCap, features],
  );

  const toggleFeature = (id: FeatureKey) => {
    setFeatures((current) => ({ ...current, [id]: !current[id] }));
  };

  const copyCode = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1400);
  };

  const downloadCode = () => {
    const url = URL.createObjectURL(new Blob([code], { type: "text/plain;charset=utf-8" }));
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${safeSymbol.toLowerCase()}-token.sol`;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  return (
    <section className="module-page token-lab-page">
      <div className="token-lab-hero">
        <div>
          <div className="module-kicker"><Code2 size={14} /> Token laboratory · EVM engineering</div>
          <div className="token-hero-row">
            <div>
              <h1>Design. Inspect. Harden. Then deploy.</h1>
              <p>
                A professional token engineering workspace for generating an auditable ERC-20
                contract template, reviewing tokenomics and checking common deployment risks.
              </p>
            </div>
            <div className="token-live-status">
              <span className={ready ? "token-status-dot ready" : "token-status-dot"} />
              <div><strong>{ready ? "Design valid" : "Review required"}</strong><span>Local generation only</span></div>
            </div>
          </div>
        </div>
        <div className="token-hero-actions">
          <button className="secondary-module-button" type="button" onClick={() => setActiveTab("security")}>
            <ShieldCheck size={13} /> Security review
          </button>
          <button className="primary-module-button" type="button" onClick={() => setActiveTab("code")}>
            <TerminalSquare size={13} /> Inspect contract
          </button>
        </div>
      </div>

      <div className="token-command-bar">
        <div><span>Network</span><strong>{selectedChain.label}</strong><small>{selectedChain.badge} · {selectedChain.fee}</small></div>
        <div><span>Contract</span><strong>{safeName}</strong><small>{safeSymbol} · Solidity 0.8.24</small></div>
        <div><span>Supply</span><strong>{Number(safeSupply).toLocaleString()} {safeSymbol}</strong><small>{safeDecimals} decimals</small></div>
        <div><span>Mode</span><strong>Non-custodial</strong><small>No signing · no deployment</small></div>
      </div>

      <div className="token-tabbar" role="tablist" aria-label="Token Lab sections">
        {[
          ["design", "Design studio", Layers3],
          ["code", "Contract source", Code2],
          ["security", "Security review", ShieldCheck],
        ].map(([id, label, Icon]) => (
          <button key={id} type="button" className={activeTab === id ? "active" : ""} onClick={() => setActiveTab(id as typeof activeTab)}>
            <Icon size={13} /> {label}
          </button>
        ))}
      </div>

      {activeTab === "design" && (
        <div className="token-workbench">
          <section className="workspace-panel token-config-panel">
            <div className="module-panel-head">
              <div><div className="module-kicker">01 · Contract design</div><h2>Token specification</h2></div>
              <span className="source-chip">Live preview</span>
            </div>

            <div className="token-form-grid">
              <label>Token name<input value={name} onChange={(event) => setName(event.target.value)} placeholder="FinAI Token" /></label>
              <label>Symbol<input value={symbol} onChange={(event) => setSymbol(event.target.value)} placeholder="FINAI" /></label>
              <label>Initial supply<input value={supply} onChange={(event) => setSupply(event.target.value)} inputMode="numeric" /></label>
              <label>Decimals<input type="number" min="0" max="18" value={decimals} onChange={(event) => setDecimals(event.target.value)} /></label>
              <label className="token-wide-field">Maximum supply<input value={cap} onChange={(event) => setCap(event.target.value)} disabled={!features.capped} inputMode="numeric" /><small>Only enforced when Supply cap is enabled.</small></label>
              <label className="token-wide-field">Target network<select value={chain} onChange={(event) => setChain(event.target.value as typeof chain)}>{chainMeta.map((item) => <option key={item.id} value={item.id}>{item.label} · {item.badge} · {item.fee}</option>)}</select><small>Network selection changes deployment planning, not the generated contract.</small></label>
            </div>

            <div className="token-section-divider" />

            <div className="module-panel-head compact">
              <div><div className="module-kicker">02 · Capability modules</div><h2>Choose the contract surface</h2></div>
            </div>
            <div className="token-feature-grid">
              {featureMeta.map((feature) => {
                const Icon = feature.icon;
                const enabled = features[feature.id];
                return (
                  <button key={feature.id} type="button" className={`token-feature-card ${enabled ? "active" : ""}`} onClick={() => toggleFeature(feature.id)}>
                    <div className="token-feature-icon"><Icon size={15} /></div>
                    <div><strong>{feature.label}</strong><span>{feature.description}</span></div>
                    <span className={`token-toggle ${enabled ? "on" : ""}`}>{enabled ? <Check size={10} /> : ""}</span>
                  </button>
                );
              })}
            </div>
          </section>

          <aside className="token-preview-column">
            <section className="workspace-panel token-identity-card">
              <div className="token-coin"><WalletCards size={23} /></div>
              <div className="token-identity-main">
                <span>Token identity</span><h2>{safeName}</h2><strong>{safeSymbol}</strong>
              </div>
              <div className="token-address-preview"><span>Contract</span><code>Generated locally · not deployed</code></div>
              <div className="token-mini-grid">
                <div><span>Supply</span><strong>{Number(safeSupply).toLocaleString()}</strong></div>
                <div><span>Decimals</span><strong>{safeDecimals}</strong></div>
                <div><span>Chain</span><strong>{selectedChain.label}</strong></div>
                <div><span>Features</span><strong>{Object.values(features).filter(Boolean).length}</strong></div>
              </div>
            </section>

            <section className="workspace-panel token-readiness-card">
              <div className="module-panel-head"><div><div className="module-kicker">Engineering gate</div><h2>Pre-deployment readiness</h2></div><Gauge size={15} /></div>
              <div className="token-readiness-meter"><i style={{ width: `${Math.round((checks.filter((check) => check.ok).length / checks.length) * 100)}%` }} /></div>
              <strong>{checks.filter((check) => check.ok).length}/{checks.length} checks clear</strong>
              <div className="token-check-list">{checks.slice(0, 4).map((check) => <div key={check.label} className={check.ok ? "ok" : "bad"}>{check.ok ? <Check size={11} /> : <CircleAlert size={11} />}<span>{check.label}</span></div>)}</div>
            </section>
          </aside>
        </div>
      )}

      {activeTab === "code" && (
        <div className="token-code-layout">
          <section className="workspace-panel token-code-panel">
            <div className="module-panel-head">
              <div><div className="module-kicker">03 · Generated source</div><h2>{safeSymbol.toLowerCase()}-token.sol</h2></div>
              <div className="resource-actions">
                <button type="button" className="secondary-module-button" onClick={() => void copyCode()}><Copy size={12} /> {copied ? "Copied" : "Copy source"}</button>
                <button type="button" className="secondary-module-button" onClick={downloadCode}><Download size={12} /> Export .sol</button>
              </div>
            </div>
            <div className="token-editor">
              <div className="token-editor-bar"><span>Solidity</span><span>OpenZeppelin extensions</span><span>{code.split("\n").length} lines</span></div>
              <pre className="code-window token-code-window">{code}</pre>
            </div>
          </section>
          <aside className="token-code-side">
            <section className="workspace-panel">
              <div className="module-kicker">Contract manifest</div>
              <div className="token-manifest">
                <div><span>Standard</span><strong>ERC-20</strong></div>
                <div><span>Compiler</span><strong>0.8.24</strong></div>
                <div><span>Library</span><strong>OpenZeppelin</strong></div>
                <div><span>Initial owner</span><strong>Deployer</strong></div>
                <div><span>Deployment</span><strong>Manual</strong></div>
              </div>
            </section>
            <section className="workspace-panel token-danger-card">
              <div className="module-kicker">Before deployment</div>
              <h2>Do not skip the engineering gate.</h2>
              <p>Compile against the exact OpenZeppelin version, run unit/property tests, inspect permissions and have the final bytecode audited before any public issuance.</p>
              <button type="button" className="secondary-module-button" onClick={() => setActiveTab("security")}><ShieldCheck size={12} /> Open security review</button>
            </section>
          </aside>
        </div>
      )}

      {activeTab === "security" && (
        <div className="token-security-layout">
          <section className="workspace-panel">
            <div className="module-panel-head">
              <div><div className="module-kicker">04 · Security review</div><h2>Contract risk surface</h2></div>
              <span className="source-chip">Static design checks</span>
            </div>
            <div className="token-security-grid">
              {[
                ["Owner permissions", features.pausable || features.mintable || features.capped ? "Admin-controlled functions enabled" : "No admin mutation path generated", features.pausable || features.mintable || features.capped],
                ["Supply controls", features.capped ? `Hard cap: ${Number(safeCap).toLocaleString()} ${safeSymbol}` : "No hard cap enforced", features.capped],
                ["Transfer emergency stop", features.pausable ? "Pause/unpause functions enabled" : "No pause switch", features.pausable],
                ["Approval UX", features.permit ? "EIP-2612 permit enabled" : "Standard approve flow", features.permit],
                ["Mint authority", features.mintable ? "Owner can mint after deployment" : "Fixed after initial mint", features.mintable],
                ["Custody", "No wallet, private-key or RPC secret handling", true],
              ].map(([title, detail, highlighted]) => (
                <div key={String(title)} className="token-security-item">
                  <div className={highlighted ? "token-security-icon active" : "token-security-icon"}><ShieldCheck size={14} /></div>
                  <div><strong>{String(title)}</strong><span>{String(detail)}</span></div>
                </div>
              ))}
            </div>
          </section>
          <section className="workspace-panel token-audit-panel">
            <div className="module-kicker">Audit checklist</div>
            <h2>What FinAI can verify locally</h2>
            <div className="token-check-list large">{checks.map((check) => <div key={check.label} className={check.ok ? "ok" : "bad"}>{check.ok ? <Check size={11} /> : <CircleAlert size={11} />}<span>{check.label}</span></div>)}</div>
            <div className="data-note"><CircleAlert size={12} /> These are design-time checks, not a substitute for compilation, tests or a professional smart-contract audit.</div>
          </section>
        </div>
      )}

      <div className="token-lab-footer">
        <div><ShieldCheck size={14} /><span><strong>Safe boundary:</strong> Token Lab generates and reviews source only. It never asks for a seed phrase, private key or wallet signature.</span></div>
        <div><Play size={13} /><span>Next engineering step: compile → test → static analysis → testnet deployment → audit → production deployment.</span></div>
      </div>
    </section>
  );
}

export default TokenGeneratorHub;
