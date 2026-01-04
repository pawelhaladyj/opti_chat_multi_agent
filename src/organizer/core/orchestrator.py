from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Tuple
import uuid

from organizer.core.registry import AgentRegistry
from organizer.core.types import Message, AgentResult, AgentOutput, Event, now_iso
from organizer.core.agent import Agent
from organizer.core.trace import TraceEvent


@dataclass(frozen=True)
class RoutingRule:
    keyword: str
    agent_name: str


class Orchestrator:
    """
    Orchestrator (new_design)

    Iteracja 14 (kompatybilność + ujednolicenie):
    - history: List[Message] (legacy wymagane przez testy)
    - team_conversation: List[TraceEvent] (legacy API wymagane przez testy/wrappery)
    - team_events: List[Event] (nowy, ujednolicony ślad MAS)
    """

    def __init__(self, registry: AgentRegistry, rules: Iterable[RoutingRule]):
        self._registry = registry
        self._rules = list(rules)

        self._history: List[Message] = []

        # legacy trace (dla testów i istniejących wrapperów)
        self._team_conversation: List[TraceEvent] = []

        # ujednolicony model eventów (nowy kontrakt)
        self._team_events: List[Event] = []

    @property
    def history(self) -> Tuple[Message, ...]:
        return tuple(self._history)

    @property
    def team_conversation(self) -> Tuple[TraceEvent, ...]:
        """
        Legacy API (TraceEvent: action/params/outcome/...)
        """
        return tuple(self._team_conversation)

    @property
    def team_events(self) -> Tuple[Event, ...]:
        """
        Nowy, ujednolicony event stream (Event: type/data/...)
        """
        return tuple(self._team_events)

    def reset(self) -> None:
        self._history.clear()
        self._team_conversation.clear()
        self._team_events.clear()

    def handle(self, message: Message) -> Message:
        cid = message.correlation_id or f"CID-{uuid.uuid4().hex[:12]}"
        user_msg = Message(
            sender=message.sender,
            content=message.content,
            role=message.role,
            meta=dict(message.meta),
            timestamp=message.timestamp,
            correlation_id=cid,
        )
        self._history.append(user_msg)

        agent = self._pick_agent(user_msg)

        # --- route (legacy TraceEvent + nowy Event) ---
        route_trace = TraceEvent(
            actor="orchestrator",
            action="route",
            target=getattr(agent, "name", agent.__class__.__name__),
            params={"text": user_msg.content},
            outcome="ok",
            error=None,
            timestamp=now_iso(),
            correlation_id=cid,
        )
        self._team_conversation.append(route_trace)
        self._team_events.append(route_trace.to_event())

        raw_out: AgentOutput = agent.handle(user_msg)
        result = self._normalize_agent_output(raw_out, cid)

        # --- eventy od agenta (jeśli agent zwrócił AgentResult.events) ---
        # zapisujemy tylko do nowego streamu Event (legacy TraceEvent jest tu opcjonalny w przyszłości)
        for ev in result.events:
            if ev.correlation_id is None:
                ev = Event(
                    type=ev.type,
                    actor=ev.actor,
                    target=ev.target,
                    data=dict(ev.data),
                    timestamp=ev.timestamp,
                    correlation_id=cid,
                )
            self._team_events.append(ev)

        self._history.append(result.message)

        # --- respond (legacy TraceEvent + nowy Event) ---
        respond_trace = TraceEvent(
            actor=result.message.sender,
            action="respond",
            target="user",
            params={"content": result.message.content},
            outcome="ok",
            error=None,
            timestamp=now_iso(),
            correlation_id=cid,
        )
        self._team_conversation.append(respond_trace)
        self._team_events.append(respond_trace.to_event())

        return result.message

    def handle_user_text(self, user_text: str) -> Message:
        return self.handle(Message(sender="user", content=user_text))

    def _normalize_agent_output(self, out: AgentOutput, cid: str) -> AgentResult:
        if isinstance(out, AgentResult):
            msg = out.message
            if msg.correlation_id is None:
                msg = Message(
                    sender=msg.sender,
                    content=msg.content,
                    role=msg.role,
                    meta=dict(msg.meta),
                    timestamp=msg.timestamp,
                    correlation_id=cid,
                )
            return AgentResult(message=msg, payload=out.payload, events=list(out.events))

        # legacy: agent zwrócił Message
        msg = out
        if msg.correlation_id is None:
            msg = Message(
                sender=msg.sender,
                content=msg.content,
                role=msg.role,
                meta=dict(msg.meta),
                timestamp=msg.timestamp,
                correlation_id=cid,
            )
        return AgentResult(message=msg)

    def _pick_agent(self, message: Message) -> Agent:
        content = (message.content or "").lower()
        for rule in self._rules:
            if rule.keyword.lower() in content:
                return self._registry.get(rule.agent_name)
        raise ValueError(
            "No routing rule matched the message. "
            "Add a rule or register a fallback agent."
        )
