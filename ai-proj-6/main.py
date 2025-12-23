import os
from datetime import datetime
from typing import Any, Dict, List

from fastapi import FastAPI
from pydantic import BaseModel


class EchoPayload(BaseModel):
    payload: Dict[str, Any]


app = FastAPI(title="AI Project 6 Lab Service")


@app.get("/")
def root():
    return {
        "message": "Lab container is running",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "port": os.getenv("PORT", "8080"),
        "candidateId": os.getenv("CANDIDATE_ID"),
        "labId": os.getenv("LAB_ID"),
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/items")
def list_items() -> List[Dict[str, Any]]:
    return [
        {"id": "notebook", "name": "Vector Notebook", "qty": 3},
        {"id": "token-pack", "name": "Token Pack 10k", "qty": 1},
        {"id": "gpu-minutes", "name": "GPU Minutes", "qty": 120},
    ]


@app.post("/echo")
def echo(body: EchoPayload):
    return {
        "echoedAt": datetime.utcnow().isoformat() + "Z",
        "payload": body.payload,
    }
