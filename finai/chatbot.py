import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from finai.pipeline import FinAIPipeline

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="FinAI",
    page_icon="💰",
    layout="centered",
)


# ============================================================
# INITIALIZE PIPELINE
# ============================================================

@st.cache_resource
def get_pipeline():

    return FinAIPipeline()


pipeline = get_pipeline()


# ============================================================
# HEADER
# ============================================================

st.title("💰 FinAI")

st.caption(
    "Multilingual Indian Financial AI Assistant"
)

st.info(
    "Demo mode: the application currently uses the "
    "working FinAI orchestration pipeline."
)


# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:

    st.session_state.messages = []


# ============================================================
# DISPLAY CHAT HISTORY
# ============================================================

for message in st.session_state.messages:

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )


# ============================================================
# USER INPUT
# ============================================================

prompt = st.chat_input(
    "Ask FinAI a financial question..."
)


if prompt:

    # --------------------------------------------------------
    # Display user message
    # --------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    with st.chat_message("user"):

        st.markdown(prompt)

    # --------------------------------------------------------
    # Process request
    # --------------------------------------------------------

    result = pipeline.process(
        prompt,
        authenticated=True,
        confirmed=True,
    )

    # --------------------------------------------------------
    # Build response
    # --------------------------------------------------------

    if result["status"] == "blocked":

        response = (
            "I can't process that request.\n\n"
            f"**Reason:** {result['message']}"
        )

    elif result["status"] == "tool":

        tool_result = result["tool_result"]

        if tool_result["status"] == "success":

            response = (
                f"**Intent:** `{result['intent']}`\n\n"
                f"**Tool:** `{result['tool']}`\n\n"
                f"**Result:**\n\n"
                f"```text\n"
                f"{tool_result['result']}\n"
                f"```"
            )

        else:

            response = (
                f"**Intent:** `{result['intent']}`\n\n"
                f"**Tool:** `{result['tool']}`\n\n"
                f"**Status:** {tool_result['status']}\n\n"
                f"{tool_result.get('reason', '')}"
            )

    elif result["status"] == "rag":

        context = result.get(
            "context",
            ""
        )

        response = (
            f"**Intent:** `{result['intent']}`\n\n"
            f"**Retrieved documents:** "
            f"{result['documents']}\n\n"
            "### Retrieved financial context\n\n"
            f"{context[:3000]}"
        )

    else:

        response = (
            "FinAI processed your request."
        )

    # --------------------------------------------------------
    # Display assistant response
    # --------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response,
        }
    )

    with st.chat_message("assistant"):

        st.markdown(response)