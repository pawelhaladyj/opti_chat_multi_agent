from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Tuple
import uuid

from organizer.core.registry import AgentRegistry
from organizer.core.types import Message, AgentResult, AgentOutput, Event, now_iso
from organizer.core.agent import Agent
from organizer.core.trace import TraceEvent
from organizer.core.memory import TeamMemory, TeamMemoryContext


@dataclass(frozen=True)
class RoutingRule:
    keyword: str
    agent_name: str


class Orchestrator:
    """
    Iteracja 15:
    - user_history: to co widzi user (czat)
    - team_conversation: legacy TraceEvent (route/respond) -> debug i kompatybilność
    - team_events: ujednolicone Event (pełny ślad MAS)
    - team_memory: kondensacja team_events (rolling summary + facts + scratchpad)
    """

    def __init__(
        self,
        registry: AgentRegistry,
        rules: Iterable[RoutingRule],
        *,
        summarize_every: int = 12,
        keep_recent_events: int = 20,
        keep_scratchpad: int = 12,
    ):
        self._registry = registry
        self._rules = list(rules)

        # Oś user-facing (czat)
        self._user_history: List[Message] = []

        # Oś MAS (legacy trace)
        self._team_conversation: List[TraceEvent] = []

        # Oś MAS (nowe eventy)
        self._team_events: List[Event] = []

        # Kondensacja kontekstu MAS
        self._team_memory = TeamMemory(
            summarize_every=summarize_every,
            keep_recent=keep_recent_events,
            keep_scratchpad=keep_scratchpad,
        )

    # --- kompatybilność wstecz (stare testy/CLI) ---
    @property
    def history(self) -> Tuple[Message, ...]:
        return tuple(self._user_history)

    @property
    def user_history(self) -> Tuple[Message, ...]:
        return tuple(self._user_history)

    @property
    def team_conversation(self) -> Tuple[TraceEvent, ...]:
        return tuple(self._team_conversation)

    @property
    def team_events(self) -> Tuple[Event, ...]:
        return tuple(self._team_events)

    def team_context(self) -> TeamMemoryContext:
        """
        To jest docelowy „kontekst MAS” dla koordynatora/agentów.
        """
        return self._team_memory.context()

    def reset(self) -> None:
        self._user_history.clear()
        self._team_conversation.clear()
        self._team_events.clear()
        self._team_memory.clear()

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
        self._user_history.append(user_msg)

        agent = self._pick_agent(user_msg)

        # route: TraceEvent + Event
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

        route_event = route_trace.to_event()
        self._team_events.append(route_event)
        self._team_memory.add_event(route_event)

        raw_out: AgentOutput = agent.handle(user_msg)
        result = self._normalize_agent_output(raw_out, cid)

        # eventy od agenta (jeśli agent zwrócił AgentResult.events)
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
            self._team_memory.add_event(ev)

        self._user_history.append(result.message)

        # respond: TraceEvent + Event
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

        respond_event = respond_trace.to_event()
        self._team_events.append(respond_event)
        self._team_memory.add_event(respond_event)

        # heurystyka facts: jeśli agent dał payload z faktami, agent może je dopisać,
        # ale na razie zostawiamy API do wykorzystania w iteracjach 16+
        # (np. coordinator/critic dopisuje fakty)

        return result.message

    def handle_user_text(self, user_text: str) -> Message:
        return self.handle(Message(sender="user", content=user_text))

    def add_team_facts(self, *facts: str) -> None:
        """
        Jawne API: koordynator/recovery/critic może dopisać ustalenia.
        """
        self._team_memory.add_facts(*facts)

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
