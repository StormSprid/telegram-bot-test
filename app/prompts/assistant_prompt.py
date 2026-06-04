"""Layer 3 — Interface Adapter: system prompt and message builder for the LLM."""
from __future__ import annotations
from app.schemas.models import RetrievedChunk


SYSTEM_PROMPT = """\
Ты — AI-ассистент интернет-магазина Centr Krasok (centr-krasok.kz), \
лидера продаж лакокрасочных материалов премиум-класса в Казахстане.

ПРАВИЛА:
1. Отвечай ТОЛЬКО на основе предоставленного контекста. Не придумывай информацию.
2. Отвечай на языке пользователя: русский, казахский или английский.
3. Используй «мы/наши», а не «компания».
4. Никогда не придумывай цены, адреса, телефоны — только те, что в контексте.
5. Не упоминай технические детали: чанки, RAG, контекст, LLM, промпты, базу знаний.
6. Пиши кратко, без длинных абзацев.
7. Если нужной информации нет — предложи позвонить: +7 778 061 5000.
"""


def build_messages(
    user_text: str,
    chunks: list[RetrievedChunk],
    history: list[dict],
) -> list[dict]:
    context = "\n\n".join(f"### {c.title}\n{c.content}" for c in chunks)

    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Include prior turns except the most recent user turn (we rebuild it with context).
    prior = history[:-1] if history and history[-1]["role"] == "user" else history
    messages.extend(prior)

    messages.append({
        "role": "user",
        "content": f"Контекст:\n{context}\n\nВопрос: {user_text}",
    })

    return messages
