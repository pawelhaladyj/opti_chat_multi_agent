from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class ToolError:
    """
    Ustandaryzowany błąd narzędzia (tool-a), niezależny od konkretnego providera.

    code: np. HTTP status (400/401/500) albo "EXCEPTION"
    type: kategoria (HTTP_ERROR, TIMEOUT, NO_RESULTS, EXCEPTION, itp.)
    message: czytelny opis
    provider: nazwa narzędzia/providera (np. "open-meteo", "ticketmaster", "fake_weather_api")
    request_params: parametry wywołania tool-a
    raw_response: surowa odpowiedź (opcjonalnie; np. body błędu HTTP)
    stack_trace_id: identyfikator stack trace (żeby log był krótki, a trace dało się skorelować)
    stack_trace: pełny stack trace (opcjonalnie; do diagnozy / LLM)
    """
    code: str
    type: str
    message: str
    provider: str
    request_params: Mapping[str, Any]
    raw_response: str | None
    stack_trace_id: str
    stack_trace: str | None = None
