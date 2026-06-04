"""Layer 4 — Framework: FastAPI application factory and module-level app instance."""
from __future__ import annotations
import logging

from fastapi import FastAPI

from app.api.dashboard import router as dashboard_router
from app.api.health import router as health_router
from app.api.telegram_webhook import router as telegram_router
from app.core.config import load_settings
from app.core.logging import configure_logging
from app.repositories.knowledge_repository import KnowledgeRepository
from app.services.dialog_memory import DialogMemory
from app.services.guardrails import Guardrails
from app.services.llm_service import LlmService
from app.services.metrics import metrics
from app.services.notifier import OwnerNotifier
from app.services.rag_service import RagService
from app.services.rate_limiter import RateLimiter
from app.services.retriever import Retriever
from app.services.telegram_service import TelegramService

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = load_settings()
    configure_logging(settings.log_level)

    docs = KnowledgeRepository(settings.knowledge_base_path).load_documents()
    logger.info("Loaded %d knowledge documents from %s", len(docs), settings.knowledge_base_path)

    retriever = Retriever(docs, semantic_weight=settings.semantic_weight)
    llm = LlmService(api_key=settings.do_api_key, model=settings.llm_model)
    guardrails = Guardrails(min_score=settings.retrieval_min_score)
    memory = DialogMemory(max_messages=settings.max_history_messages)
    telegram_service = TelegramService(token=settings.telegram_bot_token or "")
    notifier = OwnerNotifier(telegram_service, owner_chat_id=settings.owner_chat_id)

    rag_service = RagService(
        retriever=retriever,
        llm=llm,
        guardrails=guardrails,
        memory=memory,
        top_k=settings.retrieval_top_k,
        metrics=metrics,
        notifier=notifier,
    )
    rate_limiter = RateLimiter(
        max_messages=settings.rate_limit_messages,
        window_sec=settings.rate_limit_window_sec,
    )

    application = FastAPI(title="Centr Krasok Bot", version="1.0.0")

    @application.on_event("startup")
    async def _on_startup() -> None:
        logger.info("Dashboard: http://localhost:8000/dashboard")
    application.state.settings = settings
    application.state.telegram_service = telegram_service
    application.state.rag_service = rag_service
    application.state.rate_limiter = rate_limiter
    application.state.knowledge_document_count = len(docs)
    application.state.metrics = metrics

    application.include_router(health_router)
    application.include_router(telegram_router)
    application.include_router(dashboard_router)

    return application


app = create_app()
