from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from friend_brief.briefing import generate_grounded_brief
from friend_brief.citations import SECTION_NAMES
from friend_brief.data import company_by_symbol, load_snapshot
from friend_brief.demo import load_demo_briefs
from friend_brief.models import Brief, CompanySnapshot
from friend_brief.observability import init_sentry
from friend_brief.ollama_client import OllamaClient, OllamaError

init_sentry()

SNAPSHOT_PATH = Path(os.getenv("ARGUS_SNAPSHOT_PATH", "data/demo_snapshot.json"))
DEMO_BRIEFS_PATH = Path(os.getenv("ARGUS_DEMO_BRIEFS_PATH", "data/demo_briefs.json"))
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:4b")
SECTION_LABELS = {
    "what_changed": "What changed",
    "why_it_matters": "Why it matters",
    "bull_case": "Bull case",
    "bear_case": "Bear case",
    "watch_next": "What to watch next",
}


@st.cache_data
def cached_snapshot(path: str):
    return load_snapshot(path)


@st.cache_data
def cached_demo_briefs(path: str):
    return load_demo_briefs(path)


def render_claims(brief: Brief, company: CompanySnapshot) -> None:
    facts = {fact.id: fact for fact in company.facts}
    for section_name in SECTION_NAMES:
        st.subheader(SECTION_LABELS[section_name])
        claims = getattr(brief, section_name)
        if not claims:
            st.caption("The current snapshot does not provide enough evidence for this section.")
            continue
        for claim in claims:
            st.markdown(f"- {claim.text}")
            with st.expander("Evidence", expanded=False):
                for evidence_id in claim.evidence_ids:
                    evidence = facts[evidence_id]
                    source = (
                        f" · [{evidence.source}]({evidence.url})"
                        if evidence.url
                        else f" · {evidence.source}"
                    )
                    st.markdown(
                        f"**{evidence.label}:** {evidence.display_value}  \n"
                        f"As of {evidence.as_of or 'not dated'}{source}"
                    )


def main() -> None:
    st.set_page_config(page_title="Argus Friend Brief", page_icon="👁️", layout="centered")
    st.title("Argus Friend Brief")
    st.caption("A local, evidence-linked research translator powered by Gemma")
    st.info(
        "Research support only. This app does not provide investment recommendations, "
        "price targets, or trade instructions."
    )

    if not SNAPSHOT_PATH.exists():
        st.error(f"Snapshot not found: {SNAPSHOT_PATH}")
        st.stop()

    snapshot = cached_snapshot(str(SNAPSHOT_PATH))
    demo_briefs = cached_demo_briefs(str(DEMO_BRIEFS_PATH))
    symbols = [company.symbol for company in snapshot.companies]
    default_symbol_index = symbols.index("NVDA") if "NVDA" in symbols else 0
    symbol = st.selectbox("Company", symbols, index=default_symbol_index)
    explanation_level = st.radio(
        "Explanation style",
        ("Quick", "Plain English", "Research detail"),
        index=1,
        horizontal=True,
    )
    company = company_by_symbol(snapshot, symbol)
    latest_dates = sorted({fact.as_of for fact in company.facts if fact.as_of}, reverse=True)
    st.caption(
        f"Snapshot created {snapshot.generated_at:%Y-%m-%d %H:%M UTC} · "
        f"Latest included evidence {latest_dates[0] if latest_dates else 'not dated'} · "
        f"Model {OLLAMA_MODEL}"
    )

    live_column, demo_column = st.columns(2)
    generate_live = live_column.button(
        "Generate live with Gemma", type="primary", use_container_width=True
    )
    view_demo = demo_column.button(
        "View saved Gemma example",
        use_container_width=True,
        disabled=symbol not in demo_briefs,
        help=(
            "A pre-generated, citation-validated Gemma result for the public demo."
            if symbol in demo_briefs
            else "Saved examples are available for NVDA, VRT, and CEG."
        ),
    )

    brief = None
    if generate_live:
        client = OllamaClient(OLLAMA_BASE_URL, OLLAMA_MODEL)
        if not client.is_available():
            st.error(
                "Ollama is not reachable. Start it locally and ensure the configured Gemma "
                f"model ({OLLAMA_MODEL}) is installed."
            )
            st.stop()
        try:
            with st.spinner("Gemma is reading the evidence…"):
                brief = generate_grounded_brief(client, company, explanation_level)
        except OllamaError as exc:
            st.error(str(exc))
            st.stop()

    elif view_demo:
        brief = demo_briefs[symbol]
        st.caption("Saved public-demo result · generated locally with Gemma 3 4B")

    if brief is not None:
        st.header(brief.headline)
        render_claims(brief, company)
        if brief.limitations:
            st.subheader("Limitations")
            for limitation in brief.limitations:
                st.markdown(f"- {limitation}")


if __name__ == "__main__":
    main()
