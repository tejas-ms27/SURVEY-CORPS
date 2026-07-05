# New module for analysis phase final implementation.
"""Small Groq wrapper with multi-key rotation and graceful unavailability."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging
import os
from pathlib import Path
import time
from typing import Any

from .config import AnalysisConfig

logger = logging.getLogger(__name__)


@dataclass
class LLMCallResult:
    ok: bool
    content: str = ""
    error: str = ""
    provider: str = "groq"
    key_index: int | None = None
    rotation_events: list[dict[str, Any]] = field(default_factory=list)


class GroqKeyRotatingClient:
    """Transport-only Groq client. It has no detection logic."""

    def __init__(self, config: AnalysisConfig) -> None:
        self.config = config
        self.call_count = 0
        self.rotation_events: list[dict[str, Any]] = []
        self.last_attempted_key_labels: set[str] = set()
        self._load_dotenv()
        keys_raw = os.getenv(config.groq_api_keys_env, "").strip()
        if keys_raw:
            self.keys = [key.strip() for key in keys_raw.split(",") if key.strip()]
            self.key_labels = [f"{config.groq_api_keys_env}[{idx + 1}]" for idx in range(len(self.keys))]
        else:
            single = os.getenv(config.groq_api_key_env, "").strip()
            if single:
                self.keys = [single]
                self.key_labels = [config.groq_api_key_env]
            else:
                pairs = [
                    (f"GROQ{idx}", os.getenv(f"GROQ{idx}", "").strip())
                    for idx in range(1, 6)
                    if os.getenv(f"GROQ{idx}", "").strip()
                ]
                self.key_labels = [label for label, _ in pairs]
                self.keys = [value for _, value in pairs]
        self.status = ["active" for _ in self.keys]
        self.status_time = [0.0 for _ in self.keys]
        self.index = 0
        self._last_request_time = 0.0
        self.key_load_summary = {
            "loaded_key_count": len(self.keys),
            "loaded_key_labels": list(self.key_labels),
        }

    def _load_dotenv(self) -> None:
        """Load project .env when the surrounding app has not already done so."""
        try:
            from dotenv import load_dotenv

            load_dotenv()
            return
        except Exception:
            pass
        env_path = Path.cwd() / ".env"
        if not env_path.exists():
            return
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            os.environ.setdefault(name.strip(), value.strip().strip('"').strip("'"))

    @property
    def available(self) -> bool:
        return bool(self.keys)

    def has_active_key(self) -> bool:
        return any(status == "active" for status in self.status)

    def status_label(self) -> str:
        """Return a compact operator-facing status for UI and JSON output."""
        if not self.keys:
            return "disabled_no_key"
        active = sum(1 for status in self.status if status == "active")
        inactive = len(self.keys) - active
        if active and inactive:
            return "partial_failure"
        if active:
            return "active"
        if len(self.last_attempted_key_labels) < len(self.keys):
            return "partial_failure"
        if all(status in {"exhausted", "invalid"} for status in self.status):
            return "all_keys_exhausted"
        if all(status == "rate_limited" for status in self.status):
            return "all_keys_exhausted"
        return "all_keys_exhausted"

    def final_status_label(self) -> str:
        """Return a run-level status based on actual attempted call outcomes."""
        if not self.keys:
            return "disabled_no_key"
        if not self.rotation_events and self.call_count == 0:
            return "not_needed"

        successes = sum(1 for event in self.rotation_events if event.get("reason") == "success")
        failures = len(self.rotation_events) - successes
        if successes and failures:
            return "partial_failure"
        if successes:
            return "active"
        return "all_keys_exhausted"

    def remaining_call_budget(self) -> int | None:
        budget = int(getattr(self.config, "llm_run_max_calls", 0) or 0)
        if budget <= 0:
            return None
        return max(0, budget - self.call_count)

    def _record_event(
        self,
        idx: int,
        reason: str,
        call_context: str,
        attempt: int,
        error: str = "",
        latency_seconds: float = 0.0,
        status_code: int | None = None,
        response_body: str = "",
    ) -> dict[str, Any]:
        key_label = self.key_labels[idx] if idx < len(self.key_labels) else f"key_{idx + 1}"
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "key_label": key_label,
            "reason": reason,
            "call_context": call_context,
            "attempt": attempt,
            "latency_seconds": round(float(latency_seconds or 0.0), 3),
        }
        if status_code is not None:
            event["status_code"] = int(status_code)
        if response_body:
            event["response_body"] = response_body[:1000]
        if error:
            event["error"] = error[:500]
        self.rotation_events.append(event)
        self.last_attempted_key_labels.add(key_label)
        log_level = logging.INFO if reason == "success" else logging.WARNING
        logger.log(
            log_level,
            "Groq LLM call %s context=%s key=%s attempt=%s status=%s latency=%.3fs error=%s",
            reason,
            call_context,
            key_label,
            attempt,
            status_code if status_code is not None else "-",
            float(latency_seconds or 0.0),
            error[:180] if error else "",
        )
        return event

    def _active_index(self) -> int | None:
        now = time.monotonic()
        for offset in range(len(self.keys)):
            idx = (self.index + offset) % len(self.keys)
            if self.status[idx] == "active":
                return idx
            if (
                self.status[idx] == "rate_limited"
                and now - self.status_time[idx] >= self.config.llm_key_retry_cooldown_seconds
            ):
                self.status[idx] = "active"
                return idx
        return None

    def _throttle(self) -> None:
        interval = float(getattr(self.config, "llm_request_min_interval_seconds", 0.0) or 0.0)
        if interval <= 0:
            return
        now = time.monotonic()
        wait_for = interval - (now - self._last_request_time)
        if wait_for > 0:
            time.sleep(wait_for)

    def _retry_delay(self, attempt: int, idx: int) -> float:
        base = float(getattr(self.config, "llm_retry_base_seconds", 0.0) or 0.0)
        cap = float(getattr(self.config, "llm_retry_max_seconds", base) or base)
        if base <= 0 or cap <= 0:
            return 0.0
        jitter = min(base, 0.05 * ((idx % 5) + 1))
        return min(cap, base * (2 ** max(0, attempt - 1)) + jitter)

    def _classify_exception(self, exc: Exception) -> tuple[str, str, int | None, str]:
        status_code = getattr(exc, "status_code", None)
        response = getattr(exc, "response", None)
        if status_code is None and response is not None:
            status_code = getattr(response, "status_code", None)
        response_body = ""
        if response is not None:
            try:
                response_body = str(response.text)
            except Exception:
                response_body = str(response)
        text = f"{exc} {response_body}".lower()
        if status_code == 413 or "request too large" in text or ("requested" in text and "tokens" in text):
            return "active", "request_too_large", status_code, response_body
        if status_code == 429 or "429" in text or "rate" in text:
            return "rate_limited", "rate_limited", status_code, response_body
        if status_code in {500, 502, 503, 504} or any(token in text for token in ("timeout", "temporar", "server error")):
            return "rate_limited", "transient_error", status_code, response_body
        if status_code in {401, 403} or any(token in text for token in ("auth", "invalid_api_key", "invalid api key", "forbidden")):
            return "invalid", "auth_failed", status_code, response_body
        if status_code == 400 or "invalid_request_error" in text:
            return "active", "request_error", status_code, response_body
        if "quota" in text or "exhaust" in text:
            return "exhausted", "quota_exhausted", status_code, response_body
        return "rate_limited", "transient_error", status_code, response_body

    def _make_groq_client(self, api_key: str):
        from groq import Groq

        try:
            return Groq(api_key=api_key, max_retries=0, timeout=30)
        except TypeError:
            return Groq(api_key=api_key)

    def chat_json(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.0,
        call_context: str = "unknown",
    ) -> LLMCallResult:
        if not self.keys:
            return LLMCallResult(ok=False, error="llm_unavailable:no_keys")
        remaining = self.remaining_call_budget()
        if remaining is not None and remaining <= 0:
            return LLMCallResult(ok=False, error="llm_unavailable:run_call_budget_exhausted")
        events: list[dict[str, Any]] = []
        last_error = ""
        for attempt in range(max(1, len(self.keys))):
            idx = self._active_index()
            if idx is None:
                return LLMCallResult(ok=False, error=last_error or "llm_unavailable:all_keys_inactive", rotation_events=events)
            start = time.monotonic()
            try:
                self._throttle()
                client = self._make_groq_client(self.keys[idx])
                response = client.chat.completions.create(
                    model=self.config.llm_model,
                    temperature=temperature,
                    response_format={"type": "json_object"},
                    messages=messages,
                )
                latency = time.monotonic() - start
                self._last_request_time = time.monotonic()
                self.index = (idx + 1) % len(self.keys)
                self.call_count += 1
                events.append(self._record_event(idx, "success", call_context, attempt + 1, latency_seconds=latency))
                return LLMCallResult(
                    ok=True,
                    content=response.choices[0].message.content or "",
                    key_index=idx,
                    rotation_events=events,
                )
            except Exception as exc:  # Groq SDK exception types vary by version.
                latency = time.monotonic() - start
                self._last_request_time = time.monotonic()
                last_error = str(exc)
                status, reason, status_code, response_body = self._classify_exception(exc)
                self.status[idx] = status
                self.status_time[idx] = time.monotonic()
                next_idx = (idx + 1) % len(self.keys) if self.keys else None
                self.index = next_idx or 0
                events.append(
                    self._record_event(
                        idx,
                        reason,
                        call_context,
                        attempt + 1,
                        last_error,
                        latency_seconds=latency,
                        status_code=status_code,
                        response_body=response_body,
                    )
                )
                if reason in {"request_error", "request_too_large"}:
                    return LLMCallResult(ok=False, error=last_error or "llm_unavailable:request_error", rotation_events=events)
                if reason in {"rate_limited", "transient_error"} and attempt < len(self.keys) - 1:
                    time.sleep(self._retry_delay(attempt + 1, idx))
        return LLMCallResult(ok=False, error=last_error or "llm_unavailable:retry_failed", rotation_events=events)
