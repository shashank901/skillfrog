from __future__ import annotations

import streamlit as st
import httpx

API_BASE = "http://localhost:8100"
client = httpx.Client(base_url=API_BASE)

st.set_page_config(page_title="AI Code Reviewer Dashboard", layout="wide")
st.title("AI Code Reviewer Reports")

repo_filter = st.sidebar.text_input("Filter by Repository", "")
response = client.get("/reviews", params={"repo": repo_filter or None, "limit": 20})
response.raise_for_status()
reviews = response.json()

st.subheader("Recent Reviews")
for review in reviews["items"]:
    with st.expander(f"Review #{review['id']} - {review['file_path']}"):
        st.write(review["summary"])
        detail = client.get(f"/reviews/{review['id']}").json()
        for issue in detail["issues"]:
            st.markdown(f"**{issue['severity'].title()} - {issue['issue_type']}**")
            st.write(issue["description"])
            st.caption(issue["suggestion"])
