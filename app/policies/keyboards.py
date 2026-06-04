"""Layer 3 — Interface Adapter: Telegram inline keyboard definitions."""
from __future__ import annotations


QUICK_REPLIES_GREETING: dict = {
    "inline_keyboard": [
        [
            {"text": "Товары и бренды", "callback_data": "Ваш ассортимент?"},
            {"text": "Колеровка",        "callback_data": "Колеровка красок"},
        ],
        [
            {"text": "Доставка", "callback_data": "Доставка и самовывоз"},
            {"text": "Адреса",   "callback_data": "Адреса магазинов"},
        ],
        [
            {"text": "Дизайнерам",  "callback_data": "Условия для дизайнеров"},
            {"text": "Строителям", "callback_data": "Условия для строителей"},
        ],
    ]
}


def make_inline_keyboard(rows: list[list[dict]]) -> dict:
    return {"inline_keyboard": rows}
