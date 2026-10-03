import { useState } from "react";
import {
  Bot,
  CheckCircle2,
  Cpu,
  Database,
  FileSearch,
  Languages,
  Send,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { sendChat } from "./api/finai";
import { MarketTerminal } from "./components/MarketTerminal";

import "./index.css";

const languages = [
  "English",
  "Tamil",
  "Telugu",
  "Kannada",
  "Malayalam",
];

const personas = [
  {
    id: "neutral",
    name: "Neutral Assistant",
  },
  {
    id: "hype",
    name: "Financial Hype Man",
  },
  {
    id: "accountant",
    name: "Stern Accountant",
  },
];

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

function extractResponse(data: any): string {
  const candidates = [
    data?.response,
    data?.message,
    data?.result?.response,
    data?.result?.message,
    data?.result?.final_response,
  ];

  for (const value of candidates) {
    if (typeof value === "string" && value.trim()) {
      return value.trim();
    }
  }

  return "FinAI completed the request but returned no displayable response.";
}

function extractTrace(data: any): TraceState {
  const root = data?.result ?? data;
  const executionPlan = root?.execution_plan ?? {};
  const responseGeneration = root?.response_generation ?? {};

  const verificationPassed =
    root?.verification?.passed === true ||
    root?.claim_verification?.passed === true ||
    responseGeneration?.verification?.passed === true ||
    responseGeneration?.claim_verification?.passed === true ||
    responseGeneration?.fallback_verification?.passed === true ||
    responseGeneration?.fallback_claim_verification?.passed === true;

  return {
    intent:
      root?.router?.intent ??
      root?.intent ??
      "Completed",
    policy:
      executionPlan?.decision ??
      root?.policy?.status ??
      "Processed",
    authority:
      executionPlan?.authority_source ??
      root?.authority?.source ??
      root?.authority?.decision ??
      "Processed",
    execution:
      executionPlan?.execution_class ??
      executionPlan?.capability ??
      root?.execution?.type ??
      root?.execution?.engine ??
      "Completed",
    model:
      responseGeneration?.model_id ??
      responseGeneration?.selection?.actual_model_id ??
      root?.model?.model_id ??
      root?.model_id ??
      "Cloud LLM",
    verification:
      verificationPassed
        ? "Verified"
        : "Completed",
  };
}

function App() {
  const [language, setLanguage] = useState("English");
  const [persona, setPersona] = useState("neutral");
  const [message, setMessage] = useState("");
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [trace, setTrace] = useState<TraceState>({
    intent: "Pending",
    policy: "Pending",
    authority: "Pending",
    execution: "Pending",
    model: "Gemini",
    verification: "Ready",
  });

  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Hello! I'm FinAI. I can help with financial questions, calculations, banking support, and evidence-grounded financial information.",
    },
  ]);

  const sendMessage = async () => {
    const text = message.trim();

    if (!text || loading) {
      return;
    }

    setError("");

    setMessages((current) => [
      ...current,
      {
        role: "user",
        content: text,
      },
    ]);

    setMessage("");
    setLoading(true);

    try {
      const result = await sendChat({
        message: text,
        session_id: sessionId,
        language,
        persona,
        generate_response: true,
        max_new_tokens: 256,
      });

      if (result?.session_id) {
        setSessionId(result.session_id);
      }

      const assistantResponse = extractResponse(result);

      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: assistantResponse,
        },
      ]);

      setTrace(extractTrace(result));
    } catch (requestError) {
      const errorMessage =
        requestError instanceof Error
          ? requestError.message
          : "Unable to contact the FinAI backend.";

      setError(errorMessage);

      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content:
            "I couldn't reach the FinAI backend. Please make sure the FastAPI server is running.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-icon">
            <Bot size={24} />
          </div>

          <div>
            <h1>FinAI</h1>
            <p>Financial Intelligence Assistant</p>
          </div>
        </div>

        <div className="system-status">
          <span
            className={`status-dot ${loading ? "loading" : ""}`}
          />
          {loading ? "Processing" : "System Ready"}
        </div>
      </header>

      <main className="main-layout">
        <section className="chat-panel">
          <div className="chat-header">
            <div>
              <h2>Financial Assistant</h2>
              <p>
                Ask questions, calculate, analyze, and understand.
              </p>
            </div>

            <div className="model-badge">
              <Cpu size={15} />
              {trace.model}
            </div>
          </div>

          <div className="messages">
            {messages.map((item, index) => (
              <div
                key={`${item.role}-${index}`}
                className={`message-row ${item.role}`}
              >
                <div className="avatar">
                  {item.role === "assistant" ? (
                    <Bot size={18} />
                  ) : (
                    <Sparkles size={18} />
                  )}
                </div>

                <div className="message-content">
                  <div className="message-label">
                    {item.role === "assistant" ? "FinAI" : "You"}
                  </div>

                  <div className="message-bubble">
                    {item.content}
                  </div>
                </div>
              </div>
            ))}

            {loading && (
              <div className="message-row">
                <div className="avatar">
                  <Bot size={18} />
                </div>

                <div className="message-content">
                  <div className="message-label">FinAI</div>
                  <div className="message-bubble">
                    Processing your request...
                  </div>
                </div>
              </div>
            )}
          </div>

          {error && (
            <div
              style={{
                margin: "0 18px 12px",
                padding: "10px 12px",
                border: "1px solid #e1b9b9",
                borderRadius: "10px",
                background: "#fff7f7",
                color: "#8b3333",
                fontSize: "12px",
              }}
            >
              {error}
            </div>
          )}

          <div className="composer">
            <textarea
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              onKeyDown={(event) => {
                if (
                  event.key === "Enter" &&
                  !event.shiftKey
                ) {
                  event.preventDefault();
                  void sendMessage();
                }
              }}
              placeholder="Ask FinAI about EMI, KYC, investments, transactions..."
              rows={2}
              disabled={loading}
            />

            <button
              className="send-button"
              onClick={() => void sendMessage()}
              type="button"
              disabled={loading}
            >
              <Send size={18} />
              {loading ? "Sending..." : "Send"}
            </button>
          </div>
        </section>

        <aside className="sidebar">
          <section className="control-card">
            <div className="card-title">
              <Languages size={18} />
              Language
            </div>

            <select
              value={language}
              onChange={(event) => setLanguage(event.target.value)}
              disabled={loading}
            >
              {languages.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </section>

          <section className="control-card">
            <div className="card-title">
              <Sparkles size={18} />
              Persona
            </div>

            <select
              value={persona}
              onChange={(event) => setPersona(event.target.value)}
              disabled={loading}
            >
              {personas.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
          </section>

          <section className="xai-card">
            <div className="card-title">
              <ShieldCheck size={18} />
              Explainable AI
            </div>

            <div className="trace-row">
              <span>Intent</span>
              <strong>{trace.intent}</strong>
            </div>

            <div className="trace-row">
              <span>Policy</span>
              <strong>{trace.policy}</strong>
            </div>

            <div className="trace-row">
              <span>Authority</span>
              <strong>{trace.authority}</strong>
            </div>

            <div className="trace-row">
              <span>Execution</span>
              <strong>{trace.execution}</strong>
            </div>

            <div className="trace-row">
              <span>Model</span>
              <strong>{trace.model}</strong>
            </div>

            <div className="trace-row">
              <span>Verification</span>
              <strong className="verified">
                <CheckCircle2 size={15} />
                {trace.verification}
              </strong>
            </div>
          </section>

          <section className="source-card">
            <div className="card-title">
              <Database size={18} />
              Knowledge
            </div>

            <div className="source-item">
              <FileSearch size={16} />
              Hybrid RAG
            </div>

            <div className="source-item">
              <CheckCircle2 size={16} />
              Evidence Grounding
            </div>
          </section>
        </aside>
      </main>
    </div>
  );
}

export default App;
