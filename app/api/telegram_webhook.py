"""Layer 4 — Framework: Telegram webhook FastAPI router."""
from __future__ import annotations
import logging

from fastapi import APIRouter, Request, Response

from app.policies.keyboards import QUICK_REPLIES_GREETING
from app.router.intents import Intent
from app.router.router import detect_intent
from app.schemas.models import TelegramUpdate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/telegram")


@router.post("/webhook")
async def telegram_webhook(request: Request) -> Response:
    state = request.app.state
    settings = state.settings

    # 1. Verify secret header
    if settings.telegram_webhook_secret:
        header_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if header_secret != settings.telegram_webhook_secret:
            logger.warning("Rejected webhook: invalid secret")
            return Response(status_code=403)

    # 2. Parse body
    try:
        body = await request.json()
        update = TelegramUpdate.from_dict(body)
    except Exception as exc:
        logger.warning("Failed to parse update: %s", exc)
        return Response(status_code=200)

    tg = state.telegram_service
    rag = state.rag_service
    rate_limiter = state.rate_limiter

    # 3. Acknowledge callback query immediately
    if update.is_callback and update.message and update.message.callback_query_id:
        await tg.answer_callback_query(update.message.callback_query_id)

    # 4. Nothing to process
    if not update.message or not update.message.text:
        return Response(status_code=200)

    chat_id = update.message.chat.id
    text = update.message.text

    try:
        # 5. Rate limit
        if not rate_limiter.is_allowed(chat_id):
            wait = rate_limiter.seconds_until_allowed(chat_id)
            await tg.send_message(chat_id, f"Подождите {wait} сек. перед следующим вопросом.")
            return Response(status_code=200)

        # 6. Typing indicator
        await tg.send_typing(chat_id)

        # 7 & 8. Detect intent and respond
        intent = detect_intent(text)
        reply_markup = QUICK_REPLIES_GREETING if intent == Intent.GREETING else None

        if intent == Intent.GENERAL_RAG and settings.stream_enabled:
            stream = rag.stream_answer(chat_id, text)
            await tg.stream_to_message(
                chat_id, stream, edit_interval=settings.stream_edit_interval_tokens
            )
        else:
            result = await rag.answer(chat_id, text)
            await tg.send_long(chat_id, result.text, reply_markup=reply_markup)

    except Exception as exc:
        logger.error("Webhook handler error for chat %s: %s", chat_id, exc)

    return Response(status_code=200)
