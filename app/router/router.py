"""Layer 2 — Use Case: keyword-based intent detection, no ML required."""
from __future__ import annotations
from app.router.intents import Intent


def _norm(text: str) -> str:
    return " ".join(text.lower().replace("ё", "е").split())


def _is_latin(text: str) -> bool:
    """True when query is predominantly Latin-script (English etc.), not Russian/Kazakh."""
    latin = sum(1 for c in text if "a" <= c.lower() <= "z")
    cyrillic = sum(1 for c in text if "Ѐ" <= c <= "ӿ")
    total = latin + cyrillic
    return total >= 6 and latin / total > 0.6


_GREETING  = {"/start","start","привет","здравствуй","здравствуйте","добрый день","доброе утро","добрый вечер","сәлем","салам","hello","hi"}
_INJECTION = ("игнорируй","ignore previous","ignore all","system prompt","покажи системный","раскрой промпт","ты не бот","forget instructions","chunk","rag pipeline","системный промпт")
_CONTACTS  = ("адрес","где находится","контакт","телефон","номер","email","почта","где магазин","где офис","шоурум","ваш магазин","как доехать","как добраться","как найти")
_DELIVERY  = ("доставк","самовывоз","курьер","привезти","привезут")
_PAYMENT   = ("оплат","платеж","карта","kaspi","visa","mastercard")
_RETURNS   = ("возврат","вернуть","обмен","претензия")
_TINTING   = ("колеровк","оттенок","подбор цвет","45000","45 000","ral","ncs")
_BRANDS    = ("бренд","бренды","марк","производител","dulux","hammerite","pinotex","levis","sikkens","dufa","teknos","hygge","oikos","little greene","swiss lake","kelly-moore","master color")
_PRODUCTS  = ("товар","ассортимент","краск","лак","грунтовк","шпатлевк","штукатурк","антисептик","малярн","лкм","что продает","что есть","что предлагает")
_SERVICES  = ("услуг","чем можете помочь","что вы делает","предоставляет")
_DESIGNERS = ("дизайнер",)
_BUILDERS  = ("строител","подрядчик","бригада")
_CLIENTS   = ("клиент","партнер","покупател","заказчик")
_OVERVIEW  = ("о компании","чем занимается","что такое центр красок","расскажи о вас","кто вы")
_PRICE     = ("цена","цены","стоимост","сколько стоит","прайс")
_STOCK     = ("в наличии","есть ли","наличие","остаток")
_PROMOS    = ("акци","скидк","распродаж","спецпредлож")
_VACANCIES = ("вакансии","работа у вас","устроиться","зарплата")
_SENSITIVE = ("владелец","директор","основатель","список клиентов")
_OUT       = ("футбол","матч","погода","рецепт","плов","биткоин","как приготовить","кино","фильм")
_REPEAT    = ("повтори","повторить","еще раз","ещё раз")
_COMPARISON = (
    "чем отличается", "в чём разница", "что лучше", "что выбрать",
    "посоветуй", "порекомендуй", "какой лучше", "сравни",
    "подходит ли", "стоит ли", "как выбрать", "какую краску",
    "как правильно", "что нужно", "нужна ли", "как использовать",
    "как наносить", "какой расход", "чем покрасить", "что посоветуете",
)
_COMPANY   = ("краск","центр красок","centr krasok","магазин","товар","бренд","лак","цвет","ремонт","стен","покраск")


def detect_intent(text: str) -> Intent:
    n = _norm(text)
    s = n.strip("!.,? ")
    if s in _GREETING:                                                  return Intent.GREETING
    if any(m in n for m in _INJECTION):                                 return Intent.PROMPT_INJECTION
    if any(t in n for t in _REPEAT):                                    return Intent.REPEAT
    if any(t in n for t in _OUT) and not any(t in n for t in _COMPANY): return Intent.OUT_OF_SCOPE
    if any(t in n for t in _SENSITIVE):                                 return Intent.SENSITIVE
    if any(t in n for t in _COMPARISON):                                return Intent.GENERAL_RAG
    if _is_latin(text):                                                 return Intent.GENERAL_RAG
    if any(t in n for t in _CONTACTS):                                  return Intent.CONTACTS
    if any(t in n for t in _DELIVERY):                                  return Intent.DELIVERY
    if any(t in n for t in _PAYMENT):                                   return Intent.PAYMENT
    if any(t in n for t in _RETURNS):                                   return Intent.RETURNS
    if any(t in n for t in _TINTING):                                   return Intent.TINTING
    if any(t in n for t in _BRANDS):                                    return Intent.BRANDS
    if any(t in n for t in _DESIGNERS):                                 return Intent.DESIGNERS
    if any(t in n for t in _BUILDERS):                                  return Intent.BUILDERS
    if any(t in n for t in _CLIENTS):                                   return Intent.CLIENTS
    if any(t in n for t in _OVERVIEW):                                  return Intent.COMPANY_OVERVIEW
    if any(t in n for t in _PRODUCTS):                                  return Intent.PRODUCTS
    if any(t in n for t in _SERVICES):                                  return Intent.SERVICES
    if any(t in n for t in _PRICE):                                     return Intent.PRICE
    if any(t in n for t in _STOCK):                                     return Intent.STOCK
    if any(t in n for t in _PROMOS):                                    return Intent.PROMOTIONS
    if any(t in n for t in _VACANCIES):                                 return Intent.VACANCIES
    return Intent.GENERAL_RAG
