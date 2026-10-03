import { useEffect, useState } from "react";
import {
  BarChart3,
  Bot,
  CheckCircle2,
  Cpu,
  LockKeyhole,
  LogIn,
  LogOut,
  FileSearch,
  FileText,
  Languages,
  Menu,
  X,
  MessageSquare,
  Newspaper,
  PiggyBank,
  Send,
  ShieldCheck,
  ArrowRightLeft,
  BookOpen,
  Activity,
  Landmark,
  GraduationCap,
  Code2,
  BookMarked,
  Sparkles,
  WalletCards,
  Globe2,
  BrainCircuit,
} from "lucide-react";
import {
  authenticateSession,
  logoutSession,
  sendChat,
} from "./api/finai";
import { getFinAIModels, type FinAIModel } from "./api/models";
import { MarketTerminal } from "./components/MarketTerminal";
import { WealthWorkspace } from "./components/WealthWorkspace";
import { PlatformHome } from "./components/PlatformHome";
import InvestmentHub from "./components/InvestmentHub";
import { NewsHub } from "./components/NewsHub";
import { CryptoArbitrageHub } from "./components/CryptoArbitrageHub";
import { KnowledgeHub } from "./components/KnowledgeHub";
import { InvestmentDiaryHub } from "./components/InvestmentDiaryHub";
import { TokenGeneratorHub } from "./components/TokenGeneratorHub";
import { StudyHub } from "./components/StudyHub";
import { ResourcesHub } from "./components/ResourcesHub";
import { MarketAnalystHub } from "./components/MarketAnalystHub";
import GlobalInvestmentHub from "./components/GlobalInvestmentHub";
import { XAIExplorerHub } from "./components/XAIExplorerHub";
import CausalRiskLab from "./components/CausalRiskLab";
import { PlatformGuide } from "./components/PlatformGuide";
import "./index.css";

const languages = ["English", "Tamil", "Telugu", "Kannada", "Malayalam"];

const personas = [
  { id: "neutral", name: "Neutral Assistant" },
  { id: "hype", name: "Financial Hype Man" },
  { id: "accountant", name: "Stern Accountant" },
];

const navigation = [
  { id: "overview", label: "Overview", icon: WalletCards },
  { id: "assistant", label: "Assistant", icon: MessageSquare },
  { id: "markets", label: "Markets", icon: BarChart3 },
  { id: "investments", label: "Investments", icon: PiggyBank },
  { id: "portfolio", label: "Portfolio", icon: WalletCards },
  { id: "news", label: "News", icon: Newspaper },
  { id: "forms", label: "Tax & Forms", icon: FileText },
  { id: "arbitrage", label: "Crypto Arbitrage", icon: ArrowRightLeft },
  { id: "knowledge", label: "Knowledge", icon: BookOpen },
  { id: "analyst", label: "Market Analyst", icon: Activity },
  { id: "global", label: "Global Markets", icon: Globe2 },
  { id: "causal", label: "Causal Risk Lab", icon: BrainCircuit },
  { id: "resources", label: "Schemes & Resources", icon: Landmark },
  { id: "study", label: "Study Centre", icon: GraduationCap },
  { id: "token", label: "Token Lab", icon: Code2 },
  { id: "diary", label: "Investment Diary", icon: BookMarked },
  { id: "xai", label: "Explainability", icon: ShieldCheck },
] as const;

type Section = (typeof navigation)[number]["id"];

type Message = {
  role: "user" | "assistant";
  content: string;
};

type TraceState = {
  intent: string;
  policy: string;
  authority: string;
  execution: string;
  model: string;
  verification: string;
};

function rootOf(data: any) {
  return data?.result ?? data;
}

function extractResponse(data: any): string {
  const root = rootOf(data);
  const candidates = [
    root?.response,
    root?.message,
    root?.final_response,
  ];

  for (const value of candidates) {
    if (typeof value === "string" && value.trim()) {
      return value.trim();
    }
  }

  return "FinAI completed the request but returned no displayable response.";
}

function extractTrace(data: any): TraceState {
  const root = rootOf(data);
  const plan = root?.execution_plan ?? {};
  const generation = root?.response_generation ?? {};
  const verification = generation?.verification ?? root?.verification ?? {};

  const failed =
    root?.status === "VERIFICATION_FAILED" ||
    generation?.status === "VERIFICATION_FAILED" ||
    verification?.passed === false ||
    generation?.claim_verification?.passed === false;

  return {
    intent: root?.router?.intent ?? root?.intent ?? "Completed",
    policy: plan?.decision ?? root?.policy?.status ?? "Processed",
    authority: plan?.authority_source ?? root?.authority?.source ?? "Processed",
    execution: plan?.execution_class ?? plan?.capability ?? "Completed",
    model: generation?.model_id ?? generation?.selection?.actual_model_id ?? "Cloud LLM",
    verification: failed
      ? "Verification failed"
      : verification?.passed === true
        ? "Verified"
        : "Completed",
  };
}

function RichMessage({ textValue }: { textValue: string }) {
  const urlPattern = /(https?:\/\/[^\s)]+)/g;
  const parts = textValue.split(urlPattern);
  return (
    <>
      {parts.map((part, index) =>
        /^https?:\/\//.test(part) ? (
          <a key={index} href={part.replace(/[.,;]+$/, "")} target="_blank" rel="noreferrer" className="chat-link">
            {part}
          </a>
        ) : (
          <span key={index}>{part}</span>
        ),
      )}
    </>
  );
}

function traceValue(value: string) {
  return value.replaceAll("_", " ");
}

function AssistantWorkspace({ onNavigate }: { onNavigate: (section: Section) => void }) {
  const [language, setLanguage] = useState("English");
  const [persona, setPersona] = useState("neutral");
  const [models, setModels] = useState<FinAIModel[]>([]);
  const [modelId, setModelId] = useState("");
  const [message, setMessage] = useState("");
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [loading, setLoading] = useState(false);
  const [authBusy, setAuthBusy] = useState(false);
  const [authenticated, setAuthenticated] = useState(false);
  const [authRequired, setAuthRequired] = useState(false);
  const [pendingRequest, setPendingRequest] = useState("");
  const [confirmationRequired, setConfirmationRequired] = useState(false);
  const [error, setError] = useState("");
  const [trace, setTrace] = useState<TraceState>({
    intent: "Pending",
    policy: "Pending",
    authority: "Pending",
    execution: "Pending",
    model: "Gemini",
    verification: "Ready",
  });

  useEffect(() => {
    void getFinAIModels("financial_qa").then((data) => {
      const enabled = data.models.filter((model) => model.enabled);
      setModels(enabled);
      if (!modelId && enabled.length) setModelId(enabled[0].model_id);
    }).catch(() => setModels([]));
  }, []);

  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Welcome to FinAI. Ask about markets, investments, banking, calculations, KYC, or forms. You can also inspect how the request was routed and verified.",
    },
  ]);

  const suggestions = [
    "Show today's NIFTY 50 movement",
    "Explain mutual funds and SIP",
    "How does the stock market and order book work?",
    "Explain the history of money and finance",
    "How does Bitcoin and blockchain work?",
    "What documents are needed for KYC?",
    "Show the current tax forms and filing workflow",
    "Calculate EMI for ₹10 lakh at 8.5% for 20 years",
  ];

  const ensureSessionId = () => {
    if (sessionId) return sessionId;

    const nextId =
      typeof crypto !== "undefined" && "randomUUID" in crypto
        ? `session-${crypto.randomUUID()}`
        : `session-${Date.now()}`;

    setSessionId(nextId);
    return nextId;
  };

  const applyResult = (result: any, addAssistantMessage = true) => {
    if (result?.session_id) setSessionId(result.session_id);

    const session = result?.session ?? {};
    setAuthenticated(session.authenticated === true);

    const status = result?.status;
    const requiresAuth = status === "AUTH_REQUIRED";
    const requiresConfirmation = status === "CONFIRMATION_REQUIRED";

    setAuthRequired(requiresAuth);
    setConfirmationRequired(requiresConfirmation);

    if (requiresAuth) {
      setPendingRequest(
        session.pending_request ||
          "The previous request requires account authentication.",
      );
    } else if (!requiresConfirmation) {
      setPendingRequest("");
    }

    if (addAssistantMessage) {
      const rawResponse = extractResponse(result);
      const userFacingResponse = requiresAuth
        ? "This operation needs account authentication before FinAI can continue. Use “Sign in (demo)” in the Account access panel. This development login does not verify a real identity."
        : requiresConfirmation
          ? "Authentication is complete. This operation now needs your explicit confirmation. Use “Confirm operation” to continue."
          : rawResponse;

      setMessages((current) => [
        ...current,
        { role: "assistant", content: userFacingResponse },
      ]);
    }

    setTrace(extractTrace(result));
  };

  const sendMessage = async (textOverride?: string) => {
    const text = (textOverride ?? message).trim();
    if (!text || loading) return;

    setError("");
    setMessages((current) => [...current, { role: "user", content: text }]);
    setMessage("");
    setLoading(true);

    try {
      const result = await sendChat({
        message: text,
        session_id: sessionId,
        language,
        persona,
        generate_response: true,
        max_new_tokens: 512,
        model_id: modelId || undefined,
      });

      applyResult(result);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to contact the FinAI backend.",
      );
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: "I couldn't reach the FinAI backend. Check that FastAPI is running on port 8000.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const signIn = async () => {
    const id = ensureSessionId();
    setAuthBusy(true);
    setError("");

    try {
      await authenticateSession(id);
      setAuthenticated(true);
      setAuthRequired(false);

      if (pendingRequest) {
        const result = await sendChat({
          message: "authenticated",
          session_id: id,
          language,
          persona,
          generate_response: true,
          max_new_tokens: 512,
          model_id: modelId || undefined,
        });

        applyResult(result);
      } else {
        setMessages((current) => [
          ...current,
          {
            role: "assistant",
            content:
              "Demo account authentication is active for this session. Protected operations can now continue.",
          },
        ]);
      }
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to authenticate the session.",
      );
    } finally {
      setAuthBusy(false);
    }
  };

  const signOut = async () => {
    if (!sessionId) return;

    setAuthBusy(true);
    try {
      await logoutSession(sessionId);
      setAuthenticated(false);
      setAuthRequired(false);
      setConfirmationRequired(false);
      setPendingRequest("");
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: "The demo session has been signed out. Protected operations will request authentication again.",
        },
      ]);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to sign out the session.",
      );
    } finally {
      setAuthBusy(false);
    }
  };

  const confirmPending = async () => {
    const id = ensureSessionId();
    setAuthBusy(true);
    setError("");

    try {
      const result = await sendChat({
        message: "yes",
        session_id: id,
        language,
        persona,
        generate_response: true,
        max_new_tokens: 256,
      });

      applyResult(result);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to confirm the pending operation.",
      );
    } finally {
      setAuthBusy(false);
    }
  };

  return (
    <section className="assistant-workspace">
      <div className="assistant-main glass-panel">
        <div className="assistant-header">
          <div>
            <div className="module-kicker"><Sparkles size={13} /> Intelligence workspace</div>
            <h2>Financial assistant</h2>
            <p>Ask naturally. FinAI routes the request to the appropriate financial capability.</p>
          </div>
          <div className="model-pill"><Cpu size={13} /> {trace.model}</div>
        </div>

        <div className="assistant-messages">
          {messages.map((item, index) => (
            <div className={"chat-row " + item.role} key={item.role + index}>
              <div className="chat-avatar">
                {item.role === "assistant" ? <Bot size={16} /> : <Sparkles size={16} />}
              </div>
              <div className="chat-content">
                <span>{item.role === "assistant" ? "FINAI" : "YOU"}</span>
                <div className="chat-bubble"><RichMessage textValue={item.content} /></div>
              </div>
            </div>
          ))}

          {loading && (
            <div className="chat-row">
              <div className="chat-avatar"><Bot size={16} /></div>
              <div className="chat-content">
                <span>FINAI</span>
                <div className="chat-bubble processing"><span className="pulse-dot" /> Running financial reasoning…</div>
              </div>
            </div>
          )}
        </div>

        <div className="quick-prompts">
          {suggestions.map((suggestion) => (
            <button type="button" key={suggestion} onClick={() => void sendMessage(suggestion)} disabled={loading}>
              <ArrowPrompt />
              {suggestion}
            </button>
          ))}
        </div>

        {error && <div className="assistant-error">{error}</div>}

        <div className="assistant-composer">
          <textarea
            rows={2}
            value={message}
            disabled={loading}
            placeholder="Ask about a stock, investment, loan, KYC, transaction or financial form…"
            onChange={(event) => setMessage(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                void sendMessage();
              }
            }}
          />
          <button type="button" onClick={() => void sendMessage()} disabled={loading || !message.trim()}>
            <Send size={16} />
            {loading ? "Processing" : "Send"}
          </button>
        </div>
        <div className="composer-meta">
          <span>Enter to send · Shift + Enter for a new line</span>
          <span>{sessionId ? "Session active" : "New session"}</span>
        </div>
      </div>

      <aside className="assistant-side">
        <section className="glass-panel side-card security-card">
          <div className="side-title"><LockKeyhole size={15} /> Account access</div>
          <p className="security-copy">
            {authRequired
              ? "This request is waiting for authentication. Use the demo sign-in below to continue."
              : "Protected banking actions require authentication. This local demo login is only a workflow simulation and does not verify real identity."}
          </p>
          <div className="security-status">
            <span className={authenticated ? "security-dot active" : "security-dot"} />
            <strong>{authenticated ? "Authenticated" : "Not authenticated"}</strong>
          </div>

          <div className="security-actions">
            {!authenticated ? (
              <button type="button" onClick={() => void signIn()} disabled={authBusy}>
                <LogIn size={14} />
                {authBusy ? "Signing in…" : "Sign in (demo)"}
              </button>
            ) : (
              <button type="button" onClick={() => void signOut()} disabled={authBusy}>
                <LogOut size={14} />
                {authBusy ? "Signing out…" : "Sign out"}
              </button>
            )}

            {confirmationRequired && (
              <button
                type="button"
                className="confirm-button"
                onClick={() => void confirmPending()}
                disabled={authBusy}
              >
                <CheckCircle2 size={14} />
                Confirm operation
              </button>
            )}
          </div>
        </section>

        <PlatformGuide onNavigate={(section) => onNavigate(section as Section)} />

        <section className="glass-panel side-card">
          <div className="side-title"><Languages size={15} /> Preferences</div>
          <label>Language<select value={language} onChange={(event) => setLanguage(event.target.value)} disabled={loading}>{languages.map((item) => <option key={item}>{item}</option>)}</select></label>
          <label>Persona<select value={persona} onChange={(event) => setPersona(event.target.value)} disabled={loading}>{personas.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>\n          <label>Reasoning model<select value={modelId} onChange={(event) => setModelId(event.target.value)} disabled={loading}>\n            <option value="">Automatic</option>\n            {models.map((model) => <option key={model.model_id} value={model.model_id}>{model.model_name}</option>)}\n          </select></label>
        </section>

        <section className="glass-panel side-card">
          <div className="side-title"><ShieldCheck size={15} /> Explainable AI</div>
          {[
            ["Intent", trace.intent],
            ["Policy", trace.policy],
            ["Authority", trace.authority],
            ["Execution", trace.execution],
            ["Model", trace.model],
            ["Verification", trace.verification],
          ].map(([label, value]) => (
            <div className="trace-line" key={label}>
              <span>{label}</span>
              <strong>{traceValue(value)}</strong>
            </div>
          ))}
        </section>

        <section className="glass-panel side-card evidence-mini">
          <div className="side-title"><FileSearch size={15} /> Knowledge layer</div>
          <div className="mini-status"><CheckCircle2 size={14} /> Hybrid RAG</div>
          <div className="mini-status"><CheckCircle2 size={14} /> Evidence grounding</div>
        </section>
      </aside>
    </section>
  );
}

function ArrowPrompt() {
  return <span className="prompt-arrow">↗</span>;
}

function App() {
  const [section, setSection] = useState<Section>("overview");
  const [navOpen, setNavOpen] = useState(false);

  const content = {
    overview: <PlatformHome onNavigate={(value) => setSection(value as Section)} />,
    assistant: <AssistantWorkspace onNavigate={setSection} />,
    markets: <MarketTerminal />,
    investments: <InvestmentHub />,
    portfolio: <WealthWorkspace />,
    news: <NewsHub />,
    forms: <ResourcesHub defaultCategory="Tax & Forms" />,
    arbitrage: <CryptoArbitrageHub />,
    knowledge: <KnowledgeHub />,
    analyst: <MarketAnalystHub />,
    global: <GlobalInvestmentHub />,
    causal: <CausalRiskLab />,
    resources: <ResourcesHub />,
    study: <StudyHub />,
    token: <TokenGeneratorHub />,
    diary: <InvestmentDiaryHub />,
    xai: <XAIExplorerHub />,
  }[section];

  const activeItem = navigation.find((item) => item.id === section);

  const navigate = (next: Section) => {
    setSection(next);
    setNavOpen(false);
  };

  const groupStarts = new Set<Section>([
    "overview",
    "news",
    "causal",
    "resources",
  ]);

  const groupLabels: Record<Section, string> = {
    overview: "Core",
    news: "Intelligence",
    causal: "Research",
    resources: "Tools",
    assistant: "",
    markets: "",
    investments: "",
    portfolio: "",
    forms: "",
    arbitrage: "",
    knowledge: "",
    analyst: "",
    global: "",
    study: "",
    token: "",
    diary: "",
    xai: "",
  };

  return (
    <div className="platform-shell">
      <header className="platform-topbar glass-panel">
        <button className="mobile-menu-button" type="button" aria-label="Open navigation" onClick={() => setNavOpen((open) => !open)}>
          {navOpen ? <X size={18} /> : <Menu size={18} />}
        </button>

        <button className="platform-brand" type="button" onClick={() => navigate("overview")}>
          <div className="brand-logo"><Bot size={20} /></div>
          <div>
            <strong>FinAI</strong>
            <span>Financial Intelligence Platform</span>
          </div>
        </button>

        <div className="platform-topbar-center">
          <span className="platform-breadcrumb">Workspace</span>
          <strong>{activeItem?.label ?? "Overview"}</strong>
        </div>

        <div className="platform-topbar-actions">
          <button className="ask-finai-button" type="button" onClick={() => navigate("assistant")}>
            <MessageSquare size={14} />
            Ask FinAI
          </button>
          <div className="platform-status">
            <span className="status-pip" />
            Local environment
          </div>
        </div>
      </header>

      <div className="platform-frame">
        <div className={navOpen ? "platform-nav-overlay visible" : "platform-nav-overlay"} onClick={() => setNavOpen(false)} />

        <aside className={navOpen ? "platform-sidebar open" : "platform-sidebar"}>
          <div className="sidebar-heading">
            <span>FINAI WORKSPACES</span>
            <small>Navigate without horizontal scrolling</small>
          </div>

          <nav className="sidebar-nav" aria-label="FinAI navigation">
            {navigation.map((item) => {
              const Icon = item.icon;
              const showGroup = groupStarts.has(item.id);
              return (
                <div key={item.id}>
                  {showGroup && <div className="sidebar-group-label">{groupLabels[item.id]}</div>}
                  <button
                    type="button"
                    className={section === item.id ? "active" : ""}
                    onClick={() => navigate(item.id)}
                  >
                    <Icon size={16} />
                    <span>{item.label}</span>
                    {section === item.id && <i />}
                  </button>
                </div>
              );
            })}
          </nav>

          <div className="sidebar-footer">
            <span className="status-pip" />
            <div>
              <strong>FinAI local stack</strong>
              <small>API · Research · UI</small>
            </div>
          </div>
        </aside>

        <main className="platform-content">
          <div className="platform-command-strip">
            <div>
              <span>FINAI / {activeItem?.label?.toUpperCase() ?? "OVERVIEW"}</span>
              <strong>{section === "overview" ? "Financial command center" : activeItem?.label}</strong>
            </div>
            {section !== "assistant" && (
              <button type="button" onClick={() => navigate("assistant")}>
                <MessageSquare size={13} />
                Open assistant
              </button>
            )}
          </div>
          {content}
        </main>
      </div>
    </div>
  );
}

export default App;
