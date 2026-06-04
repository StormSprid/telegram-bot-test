"""Layer 2 — Use Case: owner notifications via Telegram when the bot cannot answer."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Protocol


class TelegramSendPort(Protocol):
    async def send_message(
        self, chat_id: int, text: str, reply_markup: dict | None = None
    ) -> int | None: ...


class OwnerNotifier:
    def __init__(self, telegram_service: TelegramSendPort, owner_chat_id: int | None) -> None:
        self._tg = telegram_service
        self._owner_chat_id = owner_chat_id

    async def notify_unanswered(self, user_text: str, chat_id: int) -> None:
        if not self._owner_chat_id:
            return
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        await self._tg.send_message(
            self._owner_chat_id,
            f"Бот не смог ответить на вопрос:\n«{user_text}»\n\nChat ID: {chat_id}\n{ts}",
        )

    async def notify_error(self, error: str, chat_id: int) -> None:
        if not self._owner_chat_id:
            return
        await self._tg.send_message(
            self._owner_chat_id,
            f"Ошибка в боте:\n{error}\n\nChat ID: {chat_id}",
        )
