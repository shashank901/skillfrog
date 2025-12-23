# AI Project 6 – Minimal FastAPI Lab Service

Small FastAPI app designed for lab runner smoke tests. It echoes lab metadata, provides a couple of toy endpoints, and respects the Cloud Run `PORT` environment variable.

## Features
- `GET /` returns service status plus `CANDIDATE_ID` and `LAB_ID` (when set by lab runner).
- `GET /health` for quick health checks.
- `GET /items` returns a static inventory list.
- `POST /echo` mirrors the JSON payload back with a timestamp.

## Run locally
```bash
cd ai-proj-6
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8080
```
Open http://localhost:8080 and http://localhost:8080/docs.

## Docker build & run
```bash
docker build -t ai-proj-6 .
docker run -p 8080:8080 -e PORT=8080 ai-proj-6
```

## Lab runner usage
- Ensure `LAB_PORT=8080` (default) in `lab-runner.env` or exported.
- Start: `scripts/lab_start.sh <candidate_id> ai-proj-6 ai-proj-6`
- Stop:  `scripts/lab_stop.sh <candidate_id> ai-proj-6 ai-proj-6 <duration_seconds>`

## Tests
```bash
pytest
```
