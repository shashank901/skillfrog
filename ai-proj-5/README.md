# Multi-Agent Research Assistant – Hands-On Lab

## 1. Project Overview
- **Project Title:** Multi-Agent Research Assistant  
- **Business Problem Statement:** Students, analysts, and knowledge workers spend hours searching, synthesizing, and extracting insights from large volumes of web sources. Manual research is slow, inconsistent, and often misses important angles.  
- **Business Goals & Expected Outcomes:** Deliver an AI-powered assistant that automates research on any topic by coordinating specialized agents for searching, summarizing, and insight generation. Reduce research turnaround time, improve quality of reports, and provide users with structured outputs they can trust.  
- **Industry Context:** Knowledge management teams and consulting organizations increasingly rely on automated research assistants to stay competitive. Multi-agent orchestration is becoming a key differentiator for AI-first productivity tools.  
- **Key Features & Functional Scope:** FastAPI backend orchestrating Planner/Researcher/Summarizer agents via LangChain, Streamlit UI for topic entry and visualization, SerpAPI integration for live web results, insight extraction with citation tracking, unit tests, Docker setup, and detailed lab guide.

## 2. Functional & Non-Functional Requirements
- **Business Requirements**
  - R1: Accept a research topic or question and produce a structured report with sources.  
  - R2: Leverage a Planner agent to break the topic into sub-questions and coordinate specialized agents.  
  - R3: Researcher agent must fetch relevant web snippets via SerpAPI or cached sample data.  
  - R4: Summarizer/Insight agent synthesizes findings, highlights key takeaways, and provides actionable insights.  
  - R5: Provide API endpoint and UI for retrieving full research history with timestamps and citations.
- **User Stories & Acceptance Criteria**
  - *As a student*, I want to enter a topic and receive a concise summary with source links. **AC:** `/research` returns JSON with `summary`, `insights`, and `sources`.  
  - *As an analyst*, I want to export a structured report. **AC:** Response includes Markdown payload ready for export.  
  - *As a researcher*, I want to review agent reasoning. **AC:** `/research` includes planner steps, raw search snippets, and insight chain.  
  - *As a platform owner*, I need configuration for API keys and model selection. **AC:** `.env.example` documents all required environment variables.
- **Non-Functional Requirements**
  - Security: Handle API keys via environment variables; sanitize topic input; optional rate limiting.  
  - Performance: For default configuration produce results under 8 seconds using cached examples; support asynchronous web fetch when SerpAPI enabled.  
  - Reliability: Provide fallback responses using stubbed search data when network unavailable.  
  - Observability: Structured logging per agent step, including latency metrics.  
  - Maintainability: Modular agents with interfaces allowing easy extension (e.g., add domain-specific agents).

## 3. Solution Architecture
```mermaid
flowchart LR
    User --> Streamlit[Streamlit UI]
    Streamlit -->|POST /research| FastAPI
    subgraph Backend
        FastAPI --> Planner[Planner Agent]
        Planner --> Researcher[Researcher Agent]
        Researcher --> SearchAPI[SerpAPI or Cached Data]
        Researcher --> Evidence[(Evidence Cache)]
        Planner --> Summarizer[Summarizer/Insight Agent]
        Summarizer --> LLM[(OpenAI | LangChain LLM)]
        Summarizer --> Report[(Research Reports DB)]
    end
    FastAPI -->|GET /reports| Streamlit
```

- **Components & Interactions:** FastAPI receives topic requests, delegates to a Planner agent that generates sub-queries, Researcher agent fetches web snippets via SerpAPI or fallback cache, Summarizer agent synthesizes results and stores structured report in SQLite. Streamlit UI visualizes outputs and history.  
- **Data Flow & Integration Points:** Topic request → planner tasks → web search + evidence caching → summarization → insight extraction → persistence → UI/API consumption.  
- **API Design:**  
  - `POST /research`: Body `{ "topic": str, "max_sources": int }`; returns research summary, insights, planner steps, citations.  
  - `GET /reports`: Query `limit`, `offset`; returns recent reports metadata.  
  - `GET /reports/{id}`: Detailed report including insights and source list.  
  - `GET /health`: health check.  
- **Database Design:** SQLite tables `reports` (id, topic, summary_md, insights_json, created_at) and `sources` (id, report_id FK, title, url, snippet).

## 4. Technical Implementation
- **Tech Stack:** Python 3.11, FastAPI, LangChain (multi-agent tools/chains), SerpAPI (optional), OpenAI (or fake LLM fallback), Streamlit, SQLite + SQLModel, PyTest, Docker.  
- **Folder Structure**
  ```
  ai-proj-5/
  ├── README.md
  ├── main.py
  ├── requirements.txt
  ├── docker-compose.yml
  ├── Dockerfile
  ├── .env.example
  ├── data/
  │   └── samples/search_cache.json
  ├── src/
  │   ├── __init__.py
  │   ├── backend/
  │   │   ├── __init__.py
  │   │   ├── app.py
  │   │   ├── config.py
  │   │   ├── db.py
  │   │   ├── models.py
  │   │   ├── schemas.py
  │   │   ├── agents.py
  │   │   ├── orchestrator.py
  │   │   ├── services.py
  │   │   └── utils.py
  │   └── frontend/
  │       └── app.py
  ├── streamlit_app.py
  └── tests/
      ├── __init__.py
      ├── conftest.py
      ├── test_agents.py
      ├── test_api.py
      └── test_orchestrator.py
  ```
- **Environment Setup**
  1. `python -m venv .venv && source .venv/bin/activate`  
  2. `pip install -r requirements.txt`  
  3. Copy `.env.example` to `.env`. Set `OPENAI_API_KEY`, `SERPAPI_API_KEY` (optional), or enable fake agents for offline mode.  
  4. Run `python main.py` to start FastAPI, `streamlit run streamlit_app.py` for UI.
- **Development Guide**
  1. Inspect `config.py` for toggles (fake search results, model selection).  
  2. Review agent implementations in `agents.py` and orchestration logic in `orchestrator.py`.  
  3. Test the pipeline using `pytest` with fake data before enabling live SerpAPI.  
  4. Extend planner prompts or add domain-specific tools to `ResearcherAgent`.  
  5. Customize summarizer to output Markdown sections and insight categories.  
  6. Persist additional metadata (confidence scores, tags) by extending SQLModel models.  
  7. Containerize with Docker Compose for consistent runtime.
- **Source Code:** Backend organizes configuration, database, agent layer, orchestrator service, and API routers. Frontend uses Streamlit to collect topics, show agent steps, and display insights. Agents rely on LangChain with optional fake implementations for tests/offline use.  
- **Tests:** PyTest suite covers agent logic (planner decomposition, insight synthesis), API endpoints, and orchestrator data flow using mocked search responses.  
- **Docker:** Multi-stage Dockerfile builds dependencies, optional Docker Compose spins up API and Streamlit.  
- **Configuration:** `.env` controls API keys, model selection, and fallback behavior; safe defaults enable offline execution.

## 5. Hands-On Lab Instructions
1. **Setup Environment:** Create venv, install dependencies, configure `.env`.  
2. **Run Offline Mode:** Ensure `USE_FAKE_LLM=1` or `USE_FAKE_SEARCH=1` to test without external APIs.  
3. **Kickoff Research:** `python main.py` → POST `/research` with topic, or use Streamlit UI to trigger agent pipeline.  
4. **Inspect Agent Reasoning:** Use Streamlit timeline component or check API response to view planner steps and raw snippets.  
5. **Enable Live Search:** Add SerpAPI key to `.env`, disable fake search, rerun tests to confirm hybrid mode.  
6. **Extend Agents:** Modify `agents.py` to add specialized insight extraction (e.g., pros/cons, risk analysis). Share results via `/reports`.  
7. **Docker Deploy:** `docker compose up --build` to run API + UI, test endpoints via Postman or Streamlit.  
8. **Advanced Exercise:** Integrate additional agent (e.g., CitationValidator) or connect to knowledge base for internal documents.

## 6. Validation & Testing
- **Manual Tests**
  - Submit broad topic (“Impact of quantum computing on cybersecurity”); verify multi-step plan and cited findings.  
  - Toggle fake search mode and ensure cached snippets supply results.  
  - Inspect `/reports` for persisted history with timestamps.  
  - Validate Streamlit UI displays agent steps and insight sections clearly.
- **Automated Tests:** `pytest tests` covers planner decomposition, research pipeline, API contract, and fallback flows.  
- **Sample Data:** `data/samples/search_cache.json` includes example search responses for offline operation.  
- **Troubleshooting:**  
  - Missing API keys → enable fake modes or supply keys in `.env`.  
  - SerpAPI quota reached → fallback to cached mode or throttle requests.  
  - LLM errors → switch to deterministic summarizer or adjust prompt sizes.

## 7. Reflection & Learning Outcomes
- **Skills Practiced:** Multi-agent orchestration with LangChain, web search integration, FastAPI microservices, Streamlit visualization, automated testing, Docker packaging.  
- **Real-World Applications:** Research copilots for consulting, academic assistants, knowledge management bots, competitive intelligence tools.  
- **Next Steps / Advanced Topics:** Add vector store memory, integrate citation validation agent, support multi-language research, schedule periodic updates, deploy to serverless or Kubernetes, incorporate user feedback loops.
