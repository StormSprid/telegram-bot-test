"""Layer 2 — Use Case: context quality gate and fallback messaging."""
from __future__ import annotations
from app.schemas.models import RetrievedChunk


FALLBACK = (
    "По этому вопросу у меня недостаточно данных.\n\n"
    "Уточните у менеджера:\n"
    "+7 778 061 5000\n"
    "info@centr-krasok.kz"
)


class Guardrails:
    def __init__(self, min_score: float = 0.10) -> None:
        self._min_score = min_score

    def has_context(self, chunks: list[RetrievedChunk]) -> bool:
        return bool(chunks) and chunks[0].score >= self._min_score

    def fallback(self) -> str:
        return FALLBACK
