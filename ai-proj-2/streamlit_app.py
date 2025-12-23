from __future__ import annotations

import os

import httpx
import streamlit as st

API_BASE = os.getenv("API_BASE", "http://localhost:8100")
client = httpx.Client()

st.title("AI Code Reviewer Agent")
st.write("Send code for automated review and inspect results.")

code_input = st.text_area("Paste Python code", height=200)
repo = st.text_input("GitHub repo", "")
path = st.text_input("File path", "")
commit = st.text_input("Commit SHA", "")

if st.button("Run Review"):
    payload = {"code": code_input or None, "repository": repo or None, "file_path": path or None, "commit_sha": commit or None}
    response = client.post(f"{API_BASE}/review", json=payload)
    if response.status_code == 200:
        data = response.json()
        st.success(data["summary"])
        for issue in data["issues"]:
            st.markdown(f"- **{issue['severity'].title()} ({issue['issue_type']})**: {issue['description']}\n  - Suggestion: {issue['suggestion']}")
    else:
        st.error(response.json().get("detail", "Error running review"))
