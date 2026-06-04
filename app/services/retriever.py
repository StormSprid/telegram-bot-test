"""Layer 3 — Interface Adapter: BM25 + character-bigram Jaccard retriever (pure Python)."""
from __future__ import annotations
import math
import re
from collections import Counter

from app.schemas.models import KnowledgeDocument, RetrievedChunk


_QUERY_EXPANSION: dict[str, str] = {
    "адрес":    "контакты шоурум бутик",
    "краска":   "лкм краски покрытие",
    "краски":   "лкм покрытие",
    "доставка": "курьер самовывоз",
    "доставку": "курьер самовывоз",
    "цена":     "стоимость прайс",
    "цены":     "стоимость прайс",
    "магазин":  "шоурум бутик",
    "скидка":   "акция спецпредложение",
    "скидки":   "акции",
    "телефон":  "контакты номер",
    "номер":    "контакты телефон",
    "колер":    "оттенок цвет колеровка",
    "цвет":     "оттенок колеровка",
}


def _tokenize(text: str) -> list[str]:
    text = text.lower().replace("ё", "е")
    return re.findall(r"[а-яa-z0-9]+", text)


def _bigrams(text: str) -> set[str]:
    t = text.lower().replace("ё", "е")
    t = re.sub(r"[^а-яa-z0-9 ]", " ", t)
    t = " ".join(t.split())
    if len(t) < 2:
        return set()
    return {t[i : i + 2] for i in range(len(t) - 1)}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


class Retriever:
    """BM25 with IDF weighting combined with character-bigram Jaccard similarity."""

    _K1: float = 1.5
    _B: float = 0.75
    _TITLE_BOOST: float = 1.6

    def __init__(self, docs: list[KnowledgeDocument], semantic_weight: float = 0.35) -> None:
        self._docs = docs
        self._semantic_weight = semantic_weight

        self._tokenized: list[list[str]] = [_tokenize(f"{d.title} {d.content}") for d in docs]
        self._title_token_sets: list[set[str]] = [set(_tokenize(d.title)) for d in docs]
        self._doc_bigrams: list[set[str]] = [_bigrams(f"{d.title} {d.content}") for d in docs]

        n = len(docs)
        df: Counter[str] = Counter()
        for tokens in self._tokenized:
            for t in set(tokens):
                df[t] += 1

        self._idf: dict[str, float] = {
            term: math.log((n - freq + 0.5) / (freq + 0.5) + 1)
            for term, freq in df.items()
        }

        self._doc_lens: list[int] = [len(t) for t in self._tokenized]
        self._avg_len: float = sum(self._doc_lens) / max(1, n)

    def _expand(self, query: str) -> str:
        tokens = query.lower().replace("ё", "е").split()
        extras = [_QUERY_EXPANSION[t] for t in tokens if t in _QUERY_EXPANSION]
        return (query + " " + " ".join(extras)).strip() if extras else query

    def _bm25(self, query_terms: list[str], idx: int) -> float:
        tf_map = Counter(self._tokenized[idx])
        dl = self._doc_lens[idx]
        score = 0.0
        for term in query_terms:
            idf = self._idf.get(term, 0.0)
            if idf == 0.0:
                continue
            tf = tf_map.get(term, 0)
            norm_tf = tf * (self._K1 + 1) / (
                tf + self._K1 * (1 - self._B + self._B * dl / self._avg_len)
            )
            score += idf * norm_tf
        if any(t in self._title_token_sets[idx] for t in set(query_terms)):
            score *= self._TITLE_BOOST
        return score

    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        expanded = self._expand(query)
        query_terms = _tokenize(expanded)
        query_bg = _bigrams(expanded)

        if not query_terms:
            return []

        bm25_raw = [self._bm25(query_terms, i) for i in range(len(self._docs))]
        max_bm25 = max(bm25_raw) or 1.0
        bm25_norm = [s / max_bm25 for s in bm25_raw]

        jaccard = [_jaccard(query_bg, self._doc_bigrams[i]) for i in range(len(self._docs))]

        bm25_w = 1.0 - self._semantic_weight
        combined = [
            bm25_norm[i] * bm25_w + jaccard[i] * self._semantic_weight
            for i in range(len(self._docs))
        ]

        ranked = sorted(range(len(self._docs)), key=lambda i: combined[i], reverse=True)[:top_k]

        return [
            RetrievedChunk(
                id=self._docs[i].id,
                title=self._docs[i].title,
                content=self._docs[i].content,
                score=combined[i],
            )
            for i in ranked
        ]
