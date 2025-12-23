from __future__ import annotations

import httpx
import pandas as pd
import streamlit as st

API_BASE = "http://localhost:8200"
client = httpx.Client(base_url=API_BASE)

st.set_page_config(page_title="Data Quality Reports", layout="wide")
st.title("AI Data Quality Dashboard")

repo_filter = st.sidebar.text_input("Dataset name filter", "")
response = client.get("/reports", params={"dataset_name": repo_filter or None, "limit": 20})
response.raise_for_status()
reports = response.json()

if reports["items"]:
    df = pd.DataFrame(reports["items"])
    st.dataframe(df)
else:
    st.info("No reports yet. Submit a dataset via the API.")

report_id = st.sidebar.number_input("Report ID", min_value=1, step=1)
if st.sidebar.button("Load report"):
    detail = client.get(f"/reports/{int(report_id)}")
    if detail.status_code == 200:
        payload = detail.json()
        st.subheader(f"Report #{payload['report_id']} - {payload['dataset_name']}")
        st.write(payload["summary"])
        st.metric("Missing Rate", f"{payload['missing_rate']:.2%}")
        st.metric("Outlier Rate", f"{payload['outlier_rate']:.2%}")
        st.metric("Rows", payload["total_rows"])
        st.write("### Issues")
        for issue in payload["issues"]:
            st.markdown(f"- **{issue['severity'].title()} {issue['issue_type']}**: {issue['description']}\n  - Recommendation: {issue['recommendation']}")
    else:
        st.error(detail.json().get("detail", "Unable to load report"))
