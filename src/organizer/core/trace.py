from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from organizer.core.types import Event, now_iso


@dataclass(frozen=True)
class TraceEvent:
    """
    Legacy trace model (zgodność z wcześniejszymi commitami: ToolError/trace wrapper).

    Pola oczekiwane przez istniejące testy/tooling:
    - actor, action, target, params, outcome, error, timestamp, correlation_id
    """
    actor: str
    action: str
    target: str
    params: Dict[str, Any] = field(default_factory=dict)
    outcome: str = "ok"
    error: Optional[str] = None
    timestamp: str = field(default_factory=now_iso)
    correlation_id: Optional[str] = None

    @staticmethod
    def now_iso() -> str:
        # zachowujemy API, jeśli gdzieś było używane TraceEvent.now_iso()
        return now_iso()

    def to_event(self) -> Event:
        """
        Adapter: pozwala w przyszłości migrować TraceEvent -> Event.
        Mapowanie:
        - action -> type (gdy pasuje), w przeciwnym wypadku 'error'
        - params -> data
        """
        # bezpieczne mapowanie: dopuszczamy tylko znane typy EventType
        action = (self.action or "").lower()
        event_type = action if action in {
            "route", "decision", "tool_call", "observation", "respond", "critique", "error"
        } else "error"

        return Event(
            type=event_type,  # type: ignore[arg-type]
            actor=self.actor,
            target=self.target,
            data=dict(self.params),
            timestamp=self.timestamp,
            correlation_id=self.correlation_id,
        )
