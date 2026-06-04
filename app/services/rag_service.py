"""Layer 2 — Use Case: orchestrates retrieval, guardrails, LLM, memory, metrics, and notifications."""
from __future__ import annotations
import time
from collections.abc import AsyncIterator
from typing import Protocol

from app.policies.answer_policy import get_deterministic_answer
from app.router.intents import Intent
from app.router.router import detect_intent, detect_language
from app.schemas.models import RagAnswer, RetrievedChunk
from app.services.dialog_memory import DialogMemory
from app.services.guardrails import Guardrails


class RetrieverPort(Protocol):
    def retrieve(self, query: str, top_k: int) -> list[RetrievedChunk]: ...


class LlmPort(Protocol):
    async def answer(
        self, user_text: str, chunks: list[RetrievedChunk], history: list[dict]
    ) -> tuple[str, bool, int]: ...

    async def stream_answer(
        self, user_text: str, chunks: list[RetrievedChunk], history: list[dict]
    ) -> AsyncIterator[str]: ...

    async def translate(self, text: str, target_lang: str) -> str: ...


class MetricsPort(Protocol):
    def record_request(
        self, intent: str, used_llm: bool, response_time_ms: float, tokens_used: int = 0
    ) -> None: ...
    def record_unanswered(self, chat_id: int, user_text: str) -> None: ...


class NotifierPort(Protocol):
    async def notify_unanswered(self, user_text: str, chat_id: int) -> None: ...
    async def notify_error(self, error: str, chat_id: int) -> None: ...


class RagService:
    def __init__(
        self,
        retriever: RetrieverPort,
        llm: LlmPort,
        guardrails: Guardrails,
        memory: DialogMemory,
        top_k: int = 5,
        metrics: MetricsPort | None = None,
        notifier: NotifierPort | None = None,
    ) -> None:
        self._retriever = retriever
        self._llm = llm
        self._guardrails = guardrails
        self._memory = memory
        self._top_k = top_k
        self._metrics = metrics
        self._notifier = notifier

    async def answer(self, chat_id: int, user_text: str) -> RagAnswer:
        t0 = time.monotonic()
        text = user_text.strip()
        if not text:
            return RagAnswer(text="Напишите вопрос о Centr Krasok — отвечу.")

        intent = detect_intent(text)

        if intent == Intent.REPEAT:
            last = self._memory.get_last_answer(chat_id)
            if last:
                return RagAnswer(text=last)

        det = get_deterministic_answer(intent)
        if det:
            lang = detect_language(text)
            if lang != "ru":
                det = await self._llm.translate(det, lang)
            self._save(chat_id, text, det)
            self._rec(intent, lang != "ru", t0)
            return RagAnswer(text=det, used_llm=lang != "ru")

        chunks = self._retriever.retrieve(text, top_k=self._top_k)
        if not self._guardrails.has_context(chunks):
            fb = self._guardrails.fallback()
            self._save(chat_id, text, fb)
            self._rec(intent, False, t0)
            if self._metrics:
                self._metrics.record_unanswered(chat_id, text)
            if self._notifier:
                await self._notifier.notify_unanswered(text, chat_id)
            return RagAnswer(text=fb, sources=chunks, used_llm=False)

        answer_text, used_llm, tokens = await self._llm.answer(text, chunks, self._memory.get(chat_id))
        self._save(chat_id, text, answer_text)
        self._rec(intent, used_llm, t0, tokens)
        return RagAnswer(text=answer_text, sources=chunks, used_llm=used_llm)

    async def stream_answer(self, chat_id: int, user_text: str) -> AsyncIterator[str]:
        t0 = time.monotonic()
        text = user_text.strip()
        if not text:
            yield "Напишите вопрос о Centr Krasok — отвечу."
            return

        intent = detect_intent(text)

        if intent == Intent.REPEAT:
            last = self._memory.get_last_answer(chat_id)
            if last:
                yield last
                return

        det = get_deterministic_answer(intent)
        if det:
            lang = detect_language(text)
            if lang != "ru":
                det = await self._llm.translate(det, lang)
            self._save(chat_id, text, det)
            self._rec(intent, lang != "ru", t0)
            yield det
            return

        chunks = self._retriever.retrieve(text, top_k=self._top_k)
        if not self._guardrails.has_context(chunks):
            fb = self._guardrails.fallback()
            self._save(chat_id, text, fb)
            self._rec(intent, False, t0)
            if self._metrics:
                self._metrics.record_unanswered(chat_id, text)
            if self._notifier:
                await self._notifier.notify_unanswered(text, chat_id)
            yield fb
            return

        full = ""
        async for delta in await self._llm.stream_answer(text, chunks, self._memory.get(chat_id)):
            full += delta
            yield delta
        self._save(chat_id, text, full)
        self._rec(intent, True, t0)

    def _save(self, chat_id: int, user_text: str, answer: str) -> None:
        self._memory.add(chat_id, "user", user_text)
        self._memory.add(chat_id, "assistant", answer)

    def _rec(self, intent: Intent, used_llm: bool, t0: float, tokens: int = 0) -> None:
        if self._metrics:
            self._metrics.record_request(intent.value, used_llm, (time.monotonic() - t0) * 1000, tokens)
