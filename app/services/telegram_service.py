"""Layer 3 — Interface Adapter: pure httpx wrapper for the Telegram Bot API."""
from __future__ import annotations
import logging
from collections.abc import AsyncIterator

import httpx

logger = logging.getLogger(__name__)


def _split_text(text: str, max_len: int = 3900) -> list[str]:
    if len(text) <= max_len:
        return [text]
    parts: list[str] = []
    current = ""
    for line in text.split("\n"):
        candidate = (current + "\n" + line).lstrip("\n") if current else line
        if len(candidate) > max_len:
            if current:
                parts.append(current)
            current = line
        else:
            current = candidate
    if current:
        parts.append(current)
    return parts or [text[:max_len]]


class TelegramService:
    def __init__(self, token: str) -> None:
        self._token = token

    async def send_typing(self, chat_id: int) -> None:
        await self._call("sendChatAction", {"chat_id": chat_id, "action": "typing"})

    async def send_message(
        self, chat_id: int, text: str, reply_markup: dict | None = None
    ) -> int | None:
        payload: dict = {"chat_id": chat_id, "text": text}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        result = await self._call("sendMessage", payload)
        if result and result.get("ok"):
            return result["result"]["message_id"]
        return None

    async def edit_message(self, chat_id: int, message_id: int, text: str) -> None:
        result = await self._call(
            "editMessageText",
            {"chat_id": chat_id, "message_id": message_id, "text": text},
        )
        if result and not result.get("ok"):
            desc = result.get("description", "")
            if "message is not modified" not in desc.lower():
                logger.warning("edit_message: %s", result)

    async def answer_callback_query(self, callback_query_id: str) -> None:
        await self._call("answerCallbackQuery", {"callback_query_id": callback_query_id})

    async def stream_to_message(
        self,
        chat_id: int,
        stream: AsyncIterator[str],
        edit_interval: int = 20,
    ) -> str:
        msg_id = await self.send_message(chat_id, "Печатаю...")
        accumulated = ""
        token_count = 0
        async for delta in stream:
            accumulated += delta
            token_count += 1
            if token_count % edit_interval == 0 and msg_id:
                await self.edit_message(chat_id, msg_id, accumulated + "▌")
        if msg_id and accumulated:
            await self.edit_message(chat_id, msg_id, accumulated)
        return accumulated

    async def send_long(
        self, chat_id: int, text: str, reply_markup: dict | None = None
    ) -> None:
        parts = _split_text(text)
        for i, part in enumerate(parts):
            markup = reply_markup if i == len(parts) - 1 else None
            await self.send_message(chat_id, part, reply_markup=markup)

    async def _call(self, method: str, payload: dict) -> dict | None:
        url = f"https://api.telegram.org/bot{self._token}/{method}"
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.post(url, json=payload)
                data: dict = resp.json()
                if not data.get("ok"):
                    logger.warning("Telegram %s → %s", method, data)
                return data
        except Exception as exc:
            logger.warning("Telegram %s failed: %s", method, exc)
            return None
