from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from organizer.core.errors import ToolError


@dataclass(frozen=True)
class TraceEvent:
    """
    Jeden krok w "team trace":
    - kto wykonał (actor): np. "weather_agent", "planner_agent", "tool_runner"
    - co wykonał (action): np. "tool_call"
    - target: np. nazwa tool-a
    - params: parametry wywołania
    - outcome: "success" lub "error"
    - error: ToolError, jeśli outcome="error"
    - timestamp: ISO
    - correlation_id: id do łączenia kroków w jedną sekwencję
    """
    actor: str
    action: str
    target: str
    params: Mapping[str, Any]
    outcome: str
    error: ToolError | None
    timestamp: str
    correlation_id: str

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()
