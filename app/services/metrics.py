"""Layer 2 — Use Case: in-memory metrics collector. Thread-safe, no external dependencies."""
from __future__ import annotations
import threading
import time
from datetime import datetime, timezone


class Metrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._started_at: float = time.monotonic()
        self._started_wall: datetime = datetime.now(timezone.utc)

        self.total_requests: int = 0
        self.llm_calls: int = 0
        self.deterministic_answers: int = 0
        self.guardrail_blocks: int = 0
        self.total_tokens_used: int = 0
        self.total_response_time_ms: float = 0.0
        self.requests_by_intent: dict[str, int] = {}
        self.unanswered_questions: list[dict] = []
        self.requests_per_hour: dict[int, int] = {}
        self.errors_count: int = 0

    def record_request(
        self,
        intent: str,
        used_llm: bool,
        response_time_ms: float,
        tokens_used: int = 0,
    ) -> None:
        with self._lock:
            self.total_requests += 1
            if used_llm:
                self.llm_calls += 1
            else:
                self.deterministic_answers += 1
            self.total_tokens_used += tokens_used
            self.total_response_time_ms += response_time_ms
            self.requests_by_intent[intent] = self.requests_by_intent.get(intent, 0) + 1
            hour = datetime.now().hour
            self.requests_per_hour[hour] = self.requests_per_hour.get(hour, 0) + 1

    def record_unanswered(self, chat_id: int, user_text: str) -> None:
        with self._lock:
            self.guardrail_blocks += 1
            self.unanswered_questions.append({
                "text": user_text,
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
                "chat_id": chat_id,
            })
            if len(self.unanswered_questions) > 20:
                self.unanswered_questions = self.unanswered_questions[-20:]

    def record_error(self) -> None:
        with self._lock:
            self.errors_count += 1

    def get_stats(self) -> dict:
        with self._lock:
            uptime = time.monotonic() - self._started_at
            total = self.total_requests
            avg_rt = round(self.total_response_time_ms / total, 1) if total else 0.0
            llm_rate = round(self.llm_calls / total * 100, 1) if total else 0.0
            return {
                "total_requests": total,
                "llm_calls": self.llm_calls,
                "deterministic_answers": self.deterministic_answers,
                "guardrail_blocks": self.guardrail_blocks,
                "total_tokens_used": self.total_tokens_used,
                "total_response_time_ms": round(self.total_response_time_ms, 2),
                "requests_by_intent": dict(self.requests_by_intent),
                "unanswered_questions": list(self.unanswered_questions),
                "requests_per_hour": {str(k): v for k, v in self.requests_per_hour.items()},
                "errors_count": self.errors_count,
                "llm_rate": llm_rate,
                "avg_response_time_ms": avg_rt,
                "uptime_seconds": round(uptime, 1),
                "started_at": self._started_wall.isoformat(),
            }


metrics = Metrics()
