# Centr Krasok — Telegram-бот

Бот-ассистент для магазина лакокрасочных материалов [Centr Krasok](https://centr-krasok.kz). Отвечает на вопросы о товарах, брендах, доставке, колеровке и контактах. Для сложных вопросов использует RAG поверх внутренней базы знаний с языковой моделью через DigitalOcean Serverless Inference.

---

## Архитектура

Проект построен по Clean Architecture (Uncle Bob). Зависимости направлены строго внутрь: слои не импортируют ничего из внешних слоёв.

```
Entities → Use Cases → Interface Adapters → Frameworks & Drivers
```

| Слой | Модули |
|---|---|
| Entities | `app/schemas/models.py` |
| Use Cases | `app/router/`, `app/policies/answer_policy.py`, `app/services/guardrails.py`, `app/services/dialog_memory.py`, `app/services/rag_service.py` |
| Interface Adapters | `app/services/retriever.py`, `app/services/llm_service.py`, `app/services/telegram_service.py`, `app/services/rate_limiter.py`, `app/policies/keyboards.py`, `app/prompts/`, `app/repositories/` |
| Frameworks & Drivers | `app/api/`, `app/core/`, `app/main.py` |

### Как обрабатывается сообщение

1. Вебхук принимает обновление от Telegram
2. `detect_intent()` классифицирует запрос по ключевым словам (без LLM)
3. Если интент распознан — возвращается детерминированный ответ из `answer_policy`
4. Если интент `GENERAL_RAG` — BM25+Jaccard-ретривер ищет релевантные чанки в базе знаний, затем LLM формирует ответ на их основе
5. При стриминге ответ редактируется в чате по мере генерации

---

## Структура проекта

```
app/
├── schemas/models.py          # Сущности: TelegramUpdate, RagAnswer, RetrievedChunk и др.
├── router/
│   ├── intents.py             # Enum всех интентов
│   └── router.py              # Keyword-based классификатор
├── policies/
│   ├── answer_policy.py       # Готовые ответы на каждый интент
│   └── keyboards.py           # Inline-клавиатуры Telegram
├── services/
│   ├── rag_service.py         # Оркестратор: ретривер + LLM + память
│   ├── retriever.py           # BM25 + биграммный Jaccard (без ML-библиотек)
│   ├── llm_service.py         # Клиент DigitalOcean Serverless Inference
│   ├── telegram_service.py    # HTTP-обёртка над Telegram Bot API (httpx)
│   ├── dialog_memory.py       # История диалога per-chat (скользящее окно)
│   ├── guardrails.py          # Порог релевантности, fallback-сообщение
│   └── rate_limiter.py        # Скользящее окно, без внешних зависимостей
├── prompts/assistant_prompt.py # Системный промпт и сборка сообщений для LLM
├── repositories/
│   └── knowledge_repository.py # Парсинг Markdown базы знаний по ## секциям
├── resources/
│   └── company_knowledge.md   # База знаний: 13 разделов о компании
├── api/
│   ├── telegram_webhook.py    # POST /telegram/webhook
│   └── health.py              # GET /health
├── core/
│   ├── config.py              # Settings из переменных окружения
│   └── logging.py             # Базовая настройка логирования
└── main.py                    # Фабрика FastAPI-приложения

scripts/
└── set_webhook.py             # Регистрация вебхука через Bot API
```

---

## Требования

- Python 3.11+
- Токен Telegram-бота ([@BotFather](https://t.me/BotFather))
- API-ключ DigitalOcean Serverless Inference (опционально — без него бот работает на детерминированных ответах)
- Публичный HTTPS-эндпоинт для вебхука

---

## Установка и запуск

### Локально

```bash
git clone <repo>
cd telegram-bot-test

pip install -r requirements.txt

cp .env.example .env
# Заполните .env своими значениями

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Docker

```bash
docker build -t ck-bot .
docker run --env-file .env -p 8000:8000 ck-bot
```

---

## Конфигурация

Все параметры задаются через переменные окружения или файл `.env`:

| Переменная | По умолчанию | Описание |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | — | Токен бота от @BotFather |
| `TELEGRAM_WEBHOOK_SECRET` | — | Секрет для верификации вебхука (опционально) |
| `DO_API_KEY` | — | Ключ DigitalOcean Inference |
| `LLM_MODEL` | `meta-llama/Meta-Llama-3.1-70B-Instruct` | Модель для генерации |
| `RETRIEVAL_TOP_K` | `5` | Количество чанков для контекста |
| `RETRIEVAL_MIN_SCORE` | `0.10` | Минимальный скор релевантности |
| `SEMANTIC_WEIGHT` | `0.35` | Вес Jaccard-сходства в итоговом скоре |
| `MAX_HISTORY_MESSAGES` | `8` | Глубина истории диалога |
| `RATE_LIMIT_MESSAGES` | `12` | Сообщений в окне ограничителя |
| `RATE_LIMIT_WINDOW_SEC` | `60` | Размер окна в секундах |
| `STREAM_ENABLED` | `true` | Стриминг ответов для GENERAL_RAG |
| `STREAM_EDIT_INTERVAL_TOKENS` | `20` | Редактировать сообщение каждые N токенов |
| `LOG_LEVEL` | `INFO` | Уровень логирования |

---

## Регистрация вебхука

После деплоя выполните:

```bash
python scripts/set_webhook.py --url https://your-app.example.com
```

Вебхук будет установлен на `https://your-app.example.com/telegram/webhook`.

---

## API

| Метод | Путь | Описание |
|---|---|---|
| `POST` | `/telegram/webhook` | Вебхук для Telegram |
| `GET` | `/health` | Статус приложения |

Пример ответа `/health`:

```json
{
  "status": "ok",
  "env": "production",
  "model": "meta-llama/Meta-Llama-3.1-70B-Instruct",
  "knowledge_docs": 14,
  "stream_enabled": true
}
```

---

## Ретривер

Класс `Retriever` работает без ML-библиотек. Итоговый скор:

```
score = normalize(BM25) × 0.65 + Jaccard(биграммы) × 0.35
```

Дополнительно: ×1.6 буст за совпадение запроса с заголовком секции, расширение запроса синонимами (адрес → контакты, краска → лкм и т.д.).

---

## База знаний

Файл `app/resources/company_knowledge.md` разбит на секции по заголовкам `##`. Каждая секция становится отдельным документом в индексе. Чтобы добавить информацию — достаточно дописать новую секцию и перезапустить сервер.

---


