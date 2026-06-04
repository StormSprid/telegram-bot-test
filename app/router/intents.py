"""Layer 2 — Use Case: intent taxonomy for incoming messages."""
from __future__ import annotations
from enum import Enum


class Intent(str, Enum):
    GREETING         = "greeting"
    COMPANY_OVERVIEW = "company_overview"
    PRODUCTS         = "products"
    BRANDS           = "brands"
    SERVICES         = "services"
    TINTING          = "tinting"
    DESIGNERS        = "designers"
    BUILDERS         = "builders"
    CLIENTS          = "clients"
    CONTACTS         = "contacts"
    DELIVERY         = "delivery"
    PAYMENT          = "payment"
    RETURNS          = "returns"
    PRICE            = "price"
    STOCK            = "stock"
    PROMOTIONS       = "promotions"
    VACANCIES        = "vacancies"
    SENSITIVE        = "sensitive"
    OUT_OF_SCOPE     = "out_of_scope"
    PROMPT_INJECTION = "prompt_injection"
    REPEAT           = "repeat"
    GENERAL_RAG      = "general_rag"
