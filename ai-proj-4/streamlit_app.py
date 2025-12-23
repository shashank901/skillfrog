from __future__ import annotations

import io
import json
import os
from pathlib import Path

import httpx
import pandas as pd
import streamlit as st

API_BASE = os.getenv("API_BASE", "http://localhost:8200")
client = httpx.Client()

st.title("Run Data Quality Validation")

sample_path = Path(os.getenv("SAMPLE_PATH", "ai-proj-4/data/samples/retail_sales.csv"))
code_col1, code_col2 = st.columns(2)

with code_col1:
    uploaded = st.file_uploader("Upload CSV", type=["csv"])
    dataset_name = st.text_input("Dataset name", value="retail_sales")

with code_col2:
    st.write("Or use existing file path")
    data_path = st.text_input("Data path", value=str(sample_path))

if st.button("Validate Dataset", type="primary"):
    if uploaded is not None:
        records = uploaded.read().decode("utf-8")
        df = pd.read_csv(io.StringIO(records))
        payload = {"dataset_name": dataset_name, "records": json.loads(df.to_json(orient="records"))}
    else:
        payload = {"dataset_name": dataset_name, "data_path": data_path, "fmt": "csv"}
    response = client.post(f"{API_BASE}/validate", json=payload)
    if response.status_code == 200:
        data = response.json()
        st.success(data["summary"])
        st.json(data)
    else:
        st.error(response.json().get("detail", "Validation failed"))
