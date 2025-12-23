from __future__ import annotations

from typing import Optional

import httpx
import streamlit as st

DEFAULT_API_BASE = "http://localhost:8300"


def run_dashboard(api_base: str = DEFAULT_API_BASE) -> None:
    client = httpx.Client(base_url=api_base)

    st.set_page_config(page_title="Multi-Agent Research Assistant", layout="wide")
    st.title("🔍 Multi-Agent Research Assistant")
    st.caption("Planner • Researcher • Summarizer agents orchestrated via LangChain")

    with st.form("research-form"):
        topic = st.text_input("Research topic", placeholder="e.g., Impact of AI on supply chain resilience")
        max_sources = st.slider("Max sources per sub-task", 1, 10, 5)
        submitted = st.form_submit_button("Run Research")

    if submitted and topic:
        with st.spinner("Coordinating planner, researcher, and summarizer agents..."):
            response = client.post("/research", json={"topic": topic, "max_sources": max_sources})
        if response.status_code == 200:
            data = response.json()
            st.success("Research complete. Insight summary below.")
            st.markdown(data["summary_md"], unsafe_allow_html=True)

            with st.expander("Agent Steps", expanded=False):
                for step in data["planner_steps"]:
                    st.write(f"- {step['subtopic']}")

            st.subheader("Insights")
            for insight in data["insights"]:
                st.markdown(f"**{insight['heading']}**")
                st.write(insight["content"])

            st.subheader("Sources")
            for src in data["sources"]:
                st.markdown(f"- [{src['title']}]({src['url']}) — {src['snippet']}")
        else:
            st.error(response.json().get("detail", "Unknown error"))

    st.divider()
    history = client.get("/reports", params={"limit": 5}).json()
    if history["items"]:
        st.subheader("Recent Reports")
        for item in history["items"]:
            st.write(f"• {item['created_at']} — {item['topic']}")
    else:
        st.info("No reports yet. Run a query to generate your first summary.")
