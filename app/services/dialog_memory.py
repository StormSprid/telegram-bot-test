"""Layer 2 — Use Case: per-chat sliding-window conversation history."""
from __future__ import annotations
from collections import defaultdict, deque

Message = dict[str, str]


class DialogMemory:
    def __init__(self, max_messages: int = 8) -> None:
        self._store: defaultdict[int, deque[Message]] = defaultdict(
            lambda: deque(maxlen=max_messages)
        )

    def add(self, chat_id: int, role: str, content: str) -> None:
        self._store[chat_id].append({"role": role, "content": content})

    def get(self, chat_id: int) -> list[Message]:
        return list(self._store[chat_id])

    def get_last_answer(self, chat_id: int) -> str | None:
        for msg in reversed(self._store[chat_id]):
            if msg["role"] == "assistant":
                return msg["content"]
        return None

    def clear(self, chat_id: int) -> None:
        self._store.pop(chat_id, None)
