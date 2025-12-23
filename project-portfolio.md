# AI Hands‑On Labs Portfolio

Your single pane of glass for the curated agentic labs in this repository. Each project ships with production-grade docs, tests, Docker assets, and Backstage metadata so you can plug them straight into platform tooling.

---

## 🧭 Project Index

| Project | Highlights | Quick Commands |
| --- | --- | --- |
| **AI Personal Finance Advisor Agent**<br/>`ai-proj-1/` | FastAPI · LangChain memory · Streamlit UI · SQLite persistence. Generates personalised savings/investment guidance from income + expense data. | ```bash<br/>python ai-proj-1/main.py<br/>python -m ai-proj-1.src.backend.ingest --seed<br/>pytest ai-proj-1/tests<br/>``` |
| **AI Code Reviewer Agent**<br/>`ai-proj-2/` | FastAPI service with heuristic + LLM review pipeline, GitHub snippet fetch, and structured JSON reports for CI. | ```bash<br/>python ai-proj-2/main.py<br/>streamlit run ai-proj-2/streamlit_app.py<br/>pytest ai-proj-2/tests<br/>``` |
| **Customer Support RAG Agent**<br/>`ai-proj-3/` | Telecom FAQ retrieval-augmented chatbot using LangChain + Chroma, deterministic fallbacks, and HTML chat client. | ```bash<br/>python -m ai-proj-3.src.backend.ingest --source ai-proj-3/data/sample_faqs<br/>python ai-proj-3/main.py<br/>pytest ai-proj-3/tests<br/>``` |
| **AI Data Quality Validation Agent**<br/>`ai-proj-4/` | Pandas + scikit-learn validation engine with LangChain summaries, notebook exploration, and Streamlit dashboard. | ```bash<br/>python ai-proj-4/main.py<br/>streamlit run ai-proj-4/streamlit_app.py<br/>pytest ai-proj-4/tests<br/>``` |
| **Multi-Agent Research Assistant**<br/>`ai-proj-5/` | Planner, Researcher, and Summarizer agents automate topic investigations with SerpAPI/LLM integration and Streamlit visualization. | ```bash<br/>python ai-proj-5/main.py<br/>streamlit run ai-proj-5/streamlit_app.py<br/>pytest ai-proj-5/tests<br/>``` |

> 💡 Each project folder contains a `catalog-info.yaml`. Import it into Backstage to expose ownership, lifecycle, and metadata across your developer portal.

---

## 📦 Project Structure at a Glance

```
hol-projects/
├── ai-proj-1/  # Personal Finance Advisor Agent
├── ai-proj-2/  # AI Code Reviewer Agent
├── ai-proj-3/  # Customer Support RAG Agent
├── ai-proj-4/  # Data Quality Validation Agent
├── ai-proj-5/  # Multi-Agent Research Assistant
├── project-portfolio.md
└── index.html  # Static web variant of this portfolio
```

---

## ✨ Adding the Next Lab

1. **Clone a template** – Copy the layout from an existing `ai-proj-*` folder. Keep the standard sections (README, `main.py`, `requirements.txt`, Docker assets, tests, `catalog-info.yaml`).
2. **Implement & document** – Follow the universal lab template to ensure business context, architecture diagrams, code, tests, and student guidance are in sync.
3. **Register in Backstage** – Duplicate a `catalog-info.yaml`, update the metadata, and commit inside the new project directory.
4. **Update the portfolio** – Add a new row to the table above *and* to `index.html`.
5. **Run tests** – Execute `pytest <project>/tests` to confirm the lab is runnable end-to-end.
6. **Commit & push** – Stage the new project, updated portfolio files, and push to GitHub.

---

## 🛠 Useful Global Commands

```bash
# Activate the shared virtual environment
source .venv/bin/activate

# Run all project test suites
pytest ai-proj-1/tests ai-proj-2/tests ai-proj-3/tests ai-proj-4/tests

# Rebuild Docker images for all labs
for proj in ai-proj-{1..4}; do (cd "$proj" && docker compose build); done
```

---

Need help extending the suite or wiring these labs into a delivery pipeline? Drop a note in the AI Labs backlog and tag the `ai-labs` owner defined in each catalog file. Happy shipping! 🚀
