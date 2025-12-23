from __future__ import annotations

import logging
from typing import List, Optional

from sqlmodel import Session, select

from .config import Settings
from .github_client import GitHubClient
from .models import Issue, Review
from .reviewers import ReviewPipeline
from .schemas import IssuePayload, ReviewRequest, ReviewResponse

LOGGER = logging.getLogger(__name__)


class ReviewService:
    """Coordinates GitHub fetch, analysis, and persistence."""

    def __init__(self, settings: Settings, session: Session):
        self.settings = settings
        self.session = session
        self.pipeline = ReviewPipeline(settings)
        self.github_client = GitHubClient(settings)

    def perform_review(self, payload: ReviewRequest) -> ReviewResponse:
        code = payload.code or ""
        context_parts = []
        if payload.repository and payload.file_path:
            context_parts.append(f"Repository: {payload.repository}, file: {payload.file_path}")
            fetched = self._fetch_from_github(payload.repository, payload.file_path, payload.commit_sha)
            if fetched:
                code = fetched
            elif not code:
                raise ValueError("Unable to fetch code from GitHub and no inline code provided.")
        if not code:
            raise ValueError("Code payload is empty.")

        result = self.pipeline.review(code, " | ".join(context_parts))
        review = Review(
            repository=payload.repository,
            commit_sha=payload.commit_sha,
            file_path=payload.file_path,
            summary=result.summary,
        )
        self.session.add(review)
        self.session.flush()

        issue_models: List[Issue] = []
        for issue in result.issues:
            issue_models.append(
                Issue(
                    review_id=review.id,
                    severity=issue.severity,
                    issue_type=issue.issue_type,
                    description=issue.description,
                    suggestion=issue.suggestion,
                    line_start=issue.line_start,
                    line_end=issue.line_end,
                )
            )
        self.session.add_all(issue_models)
        self.session.commit()

        return ReviewResponse(
            id=review.id,
            summary=review.summary,
            issues=[IssuePayload(**issue.model_dump()) for issue in result.issues],
            created_at=review.created_at,
        )

    def list_reviews(self, repo: Optional[str], limit: int, offset: int) -> List[Review]:
        query = select(Review).order_by(Review.created_at.desc())
        if repo:
            query = query.where(Review.repository == repo)
        return self.session.exec(query.offset(offset).limit(limit)).all()

    def count_reviews(self, repo: Optional[str]) -> int:
        query = select(Review)
        if repo:
            query = query.where(Review.repository == repo)
        return len(self.session.exec(query).all())

    def get_review(self, review_id: int) -> Review:
        review = self.session.get(Review, review_id)
        if not review:
            raise ValueError(f"Review {review_id} not found")
        return review

    def _fetch_from_github(self, repo: str, path: str, ref: Optional[str]) -> Optional[str]:
        if not repo or not path:
            return None
        code = self.github_client.fetch_file(repo, path, ref)
        if code:
            LOGGER.info("Fetched code from GitHub repo=%s path=%s", repo, path)
        return code
