"""Layer 4 — Framework: application settings loaded from environment / .env file."""
from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str | None
    telegram_webhook_secret: str | None
    do_api_key: str | None
    llm_model: str
    knowledge_base_path: Path
    retrieval_top_k: int
    retrieval_min_score: float
    semantic_weight: float
    max_history_messages: int
    rate_limit_messages: int
    rate_limit_window_sec: int
    stream_enabled: bool
    stream_edit_interval_tokens: int
    log_level: str
    owner_chat_id: int | None


def load_settings() -> Settings:
    return Settings(
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN") or None,
        telegram_webhook_secret=os.getenv("TELEGRAM_WEBHOOK_SECRET") or None,
        do_api_key=os.getenv("DO_API_KEY") or None,
        llm_model=os.getenv("LLM_MODEL", "meta-llama/Meta-Llama-3.1-70B-Instruct"),
        knowledge_base_path=Path(
            os.getenv("KNOWLEDGE_BASE_PATH", "app/resources/company_knowledge.md")
        ),
        retrieval_top_k=int(os.getenv("RETRIEVAL_TOP_K", "5")),
        retrieval_min_score=float(os.getenv("RETRIEVAL_MIN_SCORE", "0.10")),
        semantic_weight=float(os.getenv("SEMANTIC_WEIGHT", "0.35")),
        max_history_messages=int(os.getenv("MAX_HISTORY_MESSAGES", "8")),
        rate_limit_messages=int(os.getenv("RATE_LIMIT_MESSAGES", "12")),
        rate_limit_window_sec=int(os.getenv("RATE_LIMIT_WINDOW_SEC", "60")),
        stream_enabled=os.getenv("STREAM_ENABLED", "true").lower() == "true",
        stream_edit_interval_tokens=int(os.getenv("STREAM_EDIT_INTERVAL_TOKENS", "20")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        owner_chat_id=int(os.getenv("OWNER_CHAT_ID")) if os.getenv("OWNER_CHAT_ID") else None,
    )
