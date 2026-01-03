from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Type, Any

from organizer.core.errors import ToolError
from organizer.core.trace import TraceEvent
from organizer.core.tool_runner import call_tool_with_trace


@dataclass(frozen=True)
class RetryPolicy:
    """
    Polityka ponowień dla narzędzi.

    max_attempts: ile łącznie prób (1 = bez retry)
    backoff_seconds: stały backoff (0 dla testów/szybkiego działania)
    retryable_statuses: na przyszłość (np. HTTP 429/500); na razie ToolError.code jest stringiem
    retryable_exceptions: typy wyjątków, które uznajemy za retryable (na razie ToolError.type="EXCEPTION")
    """
    max_attempts: int = 3
    backoff_seconds: float = 0.0
    retryable_statuses: tuple[str, ...] = ("429", "500", "502", "503", "504")
    retryable_error_types: tuple[str, ...] = ("EXCEPTION", "TIMEOUT", "HTTP_ERROR")

    def should_retry(self, err: ToolError, attempt_no: int) -> bool:
        """
        attempt_no: numer próby zaczynając od 1.
        """
        if attempt_no >= self.max_attempts:
            return False

        # Jeśli code wygląda jak HTTP status i jest na liście retryable
        if err.code in self.retryable_statuses:
            return True

        # Jeśli typ błędu jest retryable
        if err.type in self.retryable_error_types:
            return True

        return False


class RetryExceededError(RuntimeError):
    """
    Kontrolowany błąd, gdy retry się wyczerpie.
    Trzymamy w nim ostatni ToolError dla diagnostyki.
    """
    def __init__(self, message: str, last_error: ToolError):
        super().__init__(message)
        self.last_error = last_error


def call_tool_with_retry(
    *,
    tool_name: str,
    tool_callable: Any,
    params: dict,
    actor: str,
    correlation_id: str,
    policy: RetryPolicy,
    sleep_fn: Callable[[float], None] | None = None,
) -> tuple[Any, list[TraceEvent]]:
    """
    Wywołuje tool z retry. Zwraca:
    - wynik (jeśli finalnie sukces)
    - listę TraceEvent (każda próba osobny trace)
    Gdy retry się skończy -> rzuca RetryExceededError (kontrolowany).
    """
    traces: list[TraceEvent] = []
    sleep = sleep_fn or (lambda _: None)

    last_err: ToolError | None = None

    for attempt in range(1, policy.max_attempts + 1):
        result, trace = call_tool_with_trace(
            tool_name=tool_name,
            tool_callable=tool_callable,
            params=params,
            actor=actor,
            correlation_id=correlation_id,
        )
        traces.append(trace)

        if trace.outcome == "success":
            return result, traces

        # błąd
        last_err = trace.error
        assert last_err is not None

        if policy.should_retry(last_err, attempt_no=attempt):
            if policy.backoff_seconds > 0:
                sleep(policy.backoff_seconds)
            continue

        break

    # jeśli tu jesteśmy, retry się skończyło albo błąd nie-retryable
    assert last_err is not None
    raise RetryExceededError(
        f"Retry exceeded for tool '{tool_name}' after {policy.max_attempts} attempts.",
        last_error=last_err,
    )
