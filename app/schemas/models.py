"""Layer 1 — Entities: pure immutable data structures, no framework imports."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class KnowledgeDocument:
    id: str
    title: str
    content: str


@dataclass(frozen=True)
class RetrievedChunk:
    id: str
    title: str
    content: str
    score: float


@dataclass
class RagAnswer:
    text: str
    sources: list[RetrievedChunk] = field(default_factory=list)
    used_llm: bool = False
    streamed: bool = False


@dataclass(frozen=True)
class TelegramChat:
    id: int


@dataclass(frozen=True)
class TelegramMessage:
    message_id: int
    chat: TelegramChat
    text: str | None = None
    callback_query_id: str | None = None


@dataclass(frozen=True)
class TelegramUpdate:
    update_id: int
    message: TelegramMessage | None = None
    is_callback: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> TelegramUpdate:
        if "message" in data:
            m = data["message"]
            msg = TelegramMessage(
                message_id=m["message_id"],
                chat=TelegramChat(id=m["chat"]["id"]),
                text=m.get("text"),
            )
            return cls(update_id=data["update_id"], message=msg)
        if "callback_query" in data:
            cq = data["callback_query"]
            inner = cq.get("message", {})
            msg = TelegramMessage(
                message_id=inner.get("message_id", 0),
                chat=TelegramChat(id=inner.get("chat", {}).get("id", 0)),
                text=cq.get("data"),
                callback_query_id=cq.get("id"),
            )
            return cls(update_id=data["update_id"], message=msg, is_callback=True)
        return cls(update_id=data["update_id"])
