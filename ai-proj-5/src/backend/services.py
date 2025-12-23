from __future__ import annotations

import json
from typing import List, Optional

from sqlmodel import Session, select

from .config import Settings
from .models import ResearchReport, Source
from .orchestrator import ResearchOrchestrator
from .schemas import Insight, PlannerStep, ResearchRequest, ResearchResponse, SourcePayload


class ResearchService:
    """Application service orchestrating research workflow and persistence."""

    def __init__(self, settings: Settings, session: Session):
        self.settings = settings
        self.session = session
        self.orchestrator = ResearchOrchestrator(settings)

    def run_research(self, payload: ResearchRequest) -> ResearchResponse:
        result = self.orchestrator.run(payload.topic, payload.max_sources)

        report = ResearchReport(
            topic=payload.topic,
            summary_md=result["summary_md"],
            insights_json=json.dumps(result["insights"]),
        )
        self.session.add(report)
        self.session.flush()

        source_models: List[Source] = []
        for src in result["sources"]:
            source_models.append(Source(report_id=report.id, title=src.get("title", "Untitled"), url=src.get("url", ""), snippet=src.get("snippet", "")))
        self.session.add_all(source_models)
        self.session.commit()

        return ResearchResponse(
            report_id=report.id,
            topic=report.topic,
            summary_md=report.summary_md,
            insights=[Insight(**ins) for ins in result["insights"]],
            sources=[SourcePayload(**src) for src in result["sources"]],
            planner_steps=[PlannerStep(**step) for step in result["planner_steps"]],
            created_at=report.created_at,
        )

    def list_reports(self, limit: int, offset: int) -> List[ResearchReport]:
        query = select(ResearchReport).order_by(ResearchReport.created_at.desc()).offset(offset).limit(limit)
        return self.session.exec(query).all()

    def count_reports(self) -> int:
        return len(self.session.exec(select(ResearchReport)).all())

    def get_report(self, report_id: int) -> ResearchResponse:
        report = self.session.get(ResearchReport, report_id)
        if not report:
            raise ValueError(f"Report {report_id} not found")
        sources = self.session.exec(select(Source).where(Source.report_id == report_id)).all()
        insights = json.loads(report.insights_json)
        return ResearchResponse(
            report_id=report.id,
            topic=report.topic,
            summary_md=report.summary_md,
            insights=[Insight(**ins) for ins in insights],
            sources=[SourcePayload(title=src.title, url=src.url, snippet=src.snippet) for src in sources],
            planner_steps=[],
            created_at=report.created_at,
        )
