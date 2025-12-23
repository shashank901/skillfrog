from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlmodel import Session, SQLModel, create_engine

from .config import Settings


class Database:
    """Encapsulates SQLModel engine and session management."""

    def __init__(self, settings: Settings):
        self.settings = settings
        connect_args = {"check_same_thread": False} if "sqlite" in settings.database_url else {}
        self.engine = create_engine(settings.database_url, echo=False, connect_args=connect_args)

    def create_schema(self) -> None:
        SQLModel.metadata.create_all(self.engine)

    @contextmanager
    def session(self) -> Iterator[Session]:
        session = Session(self.engine)
        try:
            yield session
        finally:
            session.close()
