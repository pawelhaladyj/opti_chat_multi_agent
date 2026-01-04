from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional, Literal, Type, Union


# ---------- wspólne ----------

Role = Literal["user", "agent", "system", "tool", "error"]
EventType = Literal["route", "decision", "tool_call", "observation", "respond", "critique", "error"]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _role_from_sender(sender: str) -> Role:
    s = (sender or "").lower()
    if s == "user":
        return "user"
    if s == "system":
        return "system"
    if s in {"tool", "tool_runner"}:
        return "tool"
    if s == "error":
        return "error"
    return "agent"


# ---------- Message ----------

@dataclass(frozen=True)
class Message:
    """
    Jednolity model wiadomości w systemie.
    Uwaga: zachowuje kompatybilność wstecz: minimalnie sender+content.
    """
    sender: str
    content: str
    role: Role = "agent"
    meta: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=now_iso)
    correlation_id: Optional[str] = None

    def __post_init__(self) -> None:
        # jeśli ktoś tworzy Message("user", "...") bez roli -> ustawiamy sensownie
        if self.role == "agent":
            object.__setattr__(self, "role", _role_from_sender(self.sender))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sender": self.sender,
            "content": self.content,
            "role": self.role,
            "meta": dict(self.meta),
            "timestamp": self.timestamp,
            "correlation_id": self.correlation_id,
        }

    @classmethod
    def from_dict(cls: Type["Message"], data: Mapping[str, Any]) -> "Message":
        return cls(
            sender=str(data.get("sender", "")),
            content=str(data.get("content", "")),
            role=data.get("role", "agent"),
            meta=dict(data.get("meta", {})),
            timestamp=str(data.get("timestamp", now_iso())),
            correlation_id=data.get("correlation_id"),
        )


# ---------- Event (nowy, ujednolicony) ----------

@dataclass(frozen=True)
class Event:
    """
    Ujednolicony event MAS (decision/tool_call/observation/critique/...).
    """
    type: EventType
    actor: str
    target: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=now_iso)
    correlation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "actor": self.actor,
            "target": self.target,
            "data": dict(self.data),
            "timestamp": self.timestamp,
            "correlation_id": self.correlation_id,
        }

    @classmethod
    def from_dict(cls: Type["Event"], data: Mapping[str, Any]) -> "Event":
        return cls(
            type=data.get("type", "error"),
            actor=str(data.get("actor", "")),
            target=str(data.get("target", "")),
            data=dict(data.get("data", {})),
            timestamp=str(data.get("timestamp", now_iso())),
            correlation_id=data.get("correlation_id"),
        )


# ---------- ToolResult (wsteczna kompatybilność) ----------

@dataclass(frozen=True)
class ToolResult:
    """
    W repo istnieją importy `ToolResult` i wrappery retry/recovery.
    Zostaje jako sztywny model.
    """
    ok: bool
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=now_iso)
    correlation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "data": dict(self.data),
            "error": self.error,
            "meta": dict(self.meta),
            "timestamp": self.timestamp,
            "correlation_id": self.correlation_id,
        }

    @classmethod
    def from_dict(cls: Type["ToolResult"], data: Mapping[str, Any]) -> "ToolResult":
        return cls(
            ok=bool(data.get("ok", False)),
            data=dict(data.get("data", {})),
            error=data.get("error"),
            meta=dict(data.get("meta", {})),
            timestamp=str(data.get("timestamp", now_iso())),
            correlation_id=data.get("correlation_id"),
        )


# ---------- AgentResult ----------

@dataclass(frozen=True)
class AgentResult:
    """
    Standaryzacja wyniku agenta:
    - message: Message (tekst)
    - payload: opcjonalny structured payload (plan/JSON/itp.)
    - events: opcjonalne eventy MAS (np. tool_call/observation)
    """
    message: Message
    payload: Optional[Dict[str, Any]] = None
    events: List[Event] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message": self.message.to_dict(),
            "payload": dict(self.payload) if isinstance(self.payload, dict) else None,
            "events": [e.to_dict() for e in self.events],
        }

    @classmethod
    def from_dict(cls: Type["AgentResult"], data: Mapping[str, Any]) -> "AgentResult":
        msg = Message.from_dict(data.get("message", {}))
        payload = data.get("payload")
        evs_raw = data.get("events", [])
        events = [Event.from_dict(e) for e in evs_raw] if isinstance(evs_raw, list) else []
        return cls(message=msg, payload=dict(payload) if isinstance(payload, dict) else None, events=events)


# Agent może zwracać Message (legacy) albo AgentResult (nowy kontrakt)
AgentOutput = Union[Message, AgentResult]
