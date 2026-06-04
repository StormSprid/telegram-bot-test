"""Layer 3 — Interface Adapter: LLM client for DigitalOcean Serverless Inference (OpenAI-compatible)."""
from __future__ import annotations
import logging
from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from app.prompts.assistant_prompt import build_messages
from app.schemas.models import RetrievedChunk

logger = logging.getLogger(__name__)

_ERR_MSG = (
    "Не удалось получить ответ от ИИ.\n\n"
    "Обратитесь к менеджеру:\n"
    "+7 778 061 5000\n"
    "info@centr-krasok.kz"
)
_OFFLINE_NOTE = (
    "\n\nОтвет сформирован без подключения к ИИ. "
    "Для точной информации: +7 778 061 5000"
)


class LlmService:
    """Wraps AsyncOpenAI pointed at DigitalOcean inference endpoint."""

    def __init__(self, api_key: str | None, model: str) -> None:
        self._model = model
        self._client: AsyncOpenAI | None = (
            AsyncOpenAI(api_key=api_key, base_url="https://inference.do-ai.run/v1")
            if api_key
            else None
        )

    async def answer(
        self,
        user_text: str,
        chunks: list[RetrievedChunk],
        history: list[dict],
    ) -> tuple[str, bool, int]:
        if not self._client:
            return self._offline_answer(chunks), False, 0
        try:
            resp = await self._client.chat.completions.create(
                model=self._model,
                messages=build_messages(user_text, chunks, history),
                temperature=0.3,
                max_tokens=1024,
            )
            tokens = resp.usage.total_tokens if resp.usage else 0
            return (resp.choices[0].message.content or "").strip(), True, tokens
        except Exception as exc:
            logger.warning("LLM answer failed: %s", exc)
            return _ERR_MSG, False, 0

    async def translate(self, text: str, target_lang: str) -> str:
        if not self._client:
            return text
        _LANG_NAMES = {"kk": "казахский язык", "en": "английский язык"}
        lang_name = _LANG_NAMES.get(target_lang, "русский язык")
        try:
            resp = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"Переведи следующий текст на {lang_name}. "
                            "Сохрани форматирование и структуру. "
                            "Верни только перевод без пояснений."
                        ),
                    },
                    {"role": "user", "content": text},
                ],
                temperature=0.1,
                max_tokens=1024,
            )
            return (resp.choices[0].message.content or text).strip()
        except Exception as exc:
            logger.warning("Translation to %s failed: %s", target_lang, exc)
            return text

    def _make_stream(
        self, user_text: str, chunks: list[RetrievedChunk], history: list[dict]
    ) -> AsyncIterator[str]:
        client = self._client

        async def _gen() -> AsyncIterator[str]:
            try:
                stream = await client.chat.completions.create(  # type: ignore[union-attr]
                    model=self._model,
                    messages=build_messages(user_text, chunks, history),
                    temperature=0.3,
                    max_tokens=1024,
                    stream=True,
                )
                async for chunk in stream:
                    delta = chunk.choices[0].delta.content or ""
                    if delta:
                        yield delta
            except Exception as exc:
                logger.warning("LLM stream failed: %s", exc)
                yield _ERR_MSG

        return _gen()

    async def stream_answer(
        self,
        user_text: str,
        chunks: list[RetrievedChunk],
        history: list[dict],
    ) -> AsyncIterator[str]:
        if not self._client:

            async def _offline() -> AsyncIterator[str]:
                yield self._offline_answer(chunks)

            return _offline()
        return self._make_stream(user_text, chunks, history)

    def _offline_answer(self, chunks: list[RetrievedChunk]) -> str:
        facts: list[str] = []
        for chunk in chunks[:3]:
            for line in chunk.content.split("\n"):
                line = line.strip("- •*#").strip()
                if len(line) > 25:
                    facts.append(f"• {line}")
                    break
        body = "\n".join(facts)
        return (body + _OFFLINE_NOTE) if body else _OFFLINE_NOTE.strip()
