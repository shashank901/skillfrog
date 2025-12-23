from __future__ import annotations

import os

import streamlit as st

from src.frontend.app import DEFAULT_API_BASE, run_dashboard

api_base = os.getenv("API_BASE", DEFAULT_API_BASE)
run_dashboard(api_base=api_base)
