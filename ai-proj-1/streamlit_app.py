from __future__ import annotations

import os
from typing import List

import streamlit as st

from src.frontend.app import FinanceApiClient

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8001")
client = FinanceApiClient(base_url=API_BASE_URL)

st.set_page_config(page_title="AI Finance Advisor", layout="wide")
st.title("AI Personal Finance Advisor")
st.write("Analyze spending patterns, savings, and goals to receive tailored advice.")

with st.sidebar:
    st.header("Setup")
    if st.button("Load Sample Data"):
        with st.spinner("Ingesting sample transactions..."):
            result = client.ingest()
        st.success(f"Loaded {result['metrics']['users']} users and {result['metrics']['transactions']} transactions")

    users = client.get_users()
    user_names: List[str] = [user["name"] for user in users]
    selected_name = st.selectbox("Select a profile", user_names)
    selected_user = next(user for user in users if user["name"] == selected_name)
    custom_question = st.text_area(
        "Ask a question", value="What steps should I take to reach my goals?", height=120
    )

col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("Recommendation")
    if st.button("Generate Advice", type="primary"):
        with st.spinner("Generating personalized advice..."):
            response = client.recommend(selected_user["id"], custom_question)
        st.markdown(f"**Summary:** {response['summary']}")
        st.markdown("### Recommended Actions")
        for idx, action in enumerate(response["recommended_actions"], start=1):
            st.write(f"{idx}. {action}")
        st.markdown("### Investment Allocation")
        for item in response["investment_split"]:
            st.write(f"- {item}")
        st.metric("Savings Rate", f"{response['savings_rate']*100:.1f}%")
        st.metric("Projected Monthly Savings", f"${response['monthly_projection']:,.0f}")

with col_right:
    st.subheader("Conversation History")
    history = client.get_history(selected_user["id"])
    if not history:
        st.info("No prior recommendations yet.")
    else:
        for item in history:
            st.markdown(f"**You:** {item['question']}")
            st.markdown(f"**Advisor:** {item['answer']}")
            st.caption(item["created_at"])
