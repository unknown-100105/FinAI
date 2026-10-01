import json
from pathlib import Path

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent.parent
TRACE_DIR = PROJECT_ROOT / "xai" / "traces"


st.set_page_config(
    page_title="FinAI XAI Dashboard",
    page_icon="💡",
    layout="wide",
)


def load_traces():
    if not TRACE_DIR.exists():
        return []

    traces = []

    for path in sorted(
        TRACE_DIR.glob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    ):
        try:
            data = json.loads(
                path.read_text(encoding="utf-8")
            )
            traces.append(data)
        except (OSError, json.JSONDecodeError):
            continue

    return traces


def display_metric(label, value):
    st.metric(label, "N/A" if value is None else value)


st.title("💡 FinAI XAI Dashboard")
st.caption(
    "Explainability and observability view for FinAI processing traces"
)

traces = load_traces()

if not traces:
    st.warning("No XAI traces are available.")
    st.stop()


trace_labels = []

for trace in traces:
    trace_id = trace.get("trace_id", "unknown")
    intent = (
        trace.get("router", {})
        .get("intent")
    )
    status = (
        trace.get("final", {})
        .get("status")
    )

    trace_labels.append(
        f"{trace_id} | {intent or 'UNKNOWN'} | {status or 'NO STATUS'}"
    )


selected_index = st.selectbox(
    "Select trace",
    range(len(traces)),
    format_func=lambda index: trace_labels[index],
)

trace = traces[selected_index]

router = trace.get("router", {})
policy = trace.get("policy", {})
session = trace.get("session", {})
tool = trace.get("tool", {})
claims = trace.get("claims")
final = trace.get("final", {})


st.divider()

st.subheader("1. Request")

request_col1, request_col2, request_col3 = st.columns(3)

with request_col1:
    display_metric(
        "Session",
        trace.get("session_id"),
    )

with request_col2:
    display_metric(
        "Started",
        trace.get("started_at"),
    )

with request_col3:
    display_metric(
        "Completed",
        trace.get("completed_at"),
    )

st.text_area(
    "User request",
    value=str(trace.get("user_input", "")),
    height=100,
    disabled=True,
)


st.subheader("2. Intent & Router")

router_col1, router_col2, router_col3, router_col4 = st.columns(4)

with router_col1:
    display_metric(
        "Intent",
        router.get("intent"),
    )

with router_col2:
    confidence = router.get("confidence")
    display_metric(
        "Confidence",
        f"{confidence:.4f}" if isinstance(confidence, (int, float)) else confidence,
    )

with router_col3:
    margin = router.get("margin")
    display_metric(
        "Margin",
        f"{margin:.4f}" if isinstance(margin, (int, float)) else margin,
    )

with router_col4:
    display_metric(
        "Decision",
        router.get("decision"),
    )

st.write("**Reason:**", router.get("reason"))

with st.expander("Top-k router candidates"):
    st.json(router.get("top_k", []))


st.subheader("3. Risk & Policy")

policy_col1, policy_col2, policy_col3, policy_col4 = st.columns(4)

with policy_col1:
    display_metric(
        "Policy",
        policy.get("status"),
    )

with policy_col2:
    display_metric(
        "Risk",
        policy.get("risk_level"),
    )

with policy_col3:
    display_metric(
        "Authentication",
        (
            "Required"
            if policy.get("authentication_required")
            else "Not required"
        ),
    )

with policy_col4:
    display_metric(
        "Confirmation",
        (
            "Required"
            if policy.get("confirmation_required")
            else "Not required"
        ),
    )

st.write("**Authorized tool:**", policy.get("tool"))


st.subheader("4. Session State")

session_col1, session_col2, session_col3 = st.columns(3)

with session_col1:
    display_metric(
        "Authenticated",
        session.get("authenticated"),
    )

with session_col2:
    display_metric(
        "Awaiting authentication",
        session.get("awaiting_authentication"),
    )

with session_col3:
    display_metric(
        "Awaiting confirmation",
        session.get("awaiting_confirmation"),
    )

st.write("**Pending intent:**", session.get("pending_intent"))
st.write("**Pending tool:**", session.get("pending_tool"))


st.subheader("5. Execution")

tool_col1, tool_col2, tool_col3 = st.columns(3)

with tool_col1:
    display_metric(
        "Tool",
        tool.get("name"),
    )

with tool_col2:
    display_metric(
        "Executed",
        tool.get("executed"),
    )

with tool_col3:
    display_metric(
        "Success",
        tool.get("success"),
    )

st.write("**Message:**", tool.get("message"))

if tool.get("data"):
    with st.expander("Tool result data"):
        st.json(tool.get("data"))


st.subheader("6. Claims & Verification")

if claims:
    claims_col1, claims_col2, claims_col3 = st.columns(3)

    with claims_col1:
        display_metric(
            "Total claims",
            claims.get("total_count"),
        )

    with claims_col2:
        display_metric(
            "Authoritative claims",
            claims.get("authoritative_count"),
        )

    with claims_col3:
        display_metric(
            "All verified",
            claims.get("all_verified"),
        )

    with st.expander("Claim details"):
        st.json(claims.get("items", []))
else:
    st.info(
        "No claim-verification data is recorded in this trace."
    )


st.subheader("7. Final Result")

final_col1, final_col2 = st.columns(2)

with final_col1:
    display_metric(
        "Stage",
        final.get("stage"),
    )

with final_col2:
    display_metric(
        "Status",
        final.get("status"),
    )

st.write("**Message:**", final.get("message"))


st.divider()

st.caption(
    "FinAI XAI Dashboard — read-only observability layer. "
    "It does not authorize or execute financial actions."
)
