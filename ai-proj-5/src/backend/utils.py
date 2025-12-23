from __future__ import annotations

from typing import Iterable, List

from .schemas import SourcePayload


def serialize_sources(sources: Iterable[dict]) -> List[SourcePayload]:
    return [SourcePayload(**src) for src in sources]
