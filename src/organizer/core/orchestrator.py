from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Tuple
import uuid

from organizer.core.registry import AgentRegistry
from organizer.core.types import Message, AgentResult, AgentOutput, Event, now_iso
from organizer.core.trace import TraceEvent
from organizer.core.memory import TeamMemory, TeamMemoryContext
from organizer.core.decision import CoordinatorDecision


@dataclass(frozen=True)
class RoutingRule:
    keyword: str
    agent_name: str


class DefaultCoordinator:
    """
    Fallback koordynator (deterministyczny), używany gdy nie zarejestrowano agenta 'coordinator'.

    Ważne: to nadal Coordinator podejmuje decyzję — Orchestrator nie routuje sam.
    Wykorzystujemy legacy RoutingRule jako reguły decyzyjne koordynatora, żeby nie psuć starych testów.
    """

    name = "coordinator"

    def __init__(self, rules: List[RoutingRule]):
        self._rules = rules

    def decide(self, *, user_goal: str, team_ctx: TeamMemoryContext, agents: list) -> CoordinatorDecision:
        text = (user_goal or "")
        low = text.lower()

        for rule in self._rules:
            if rule.keyword.lower() in low:
                return CoordinatorDecision(
                    next_agent=rule.agent_name,
                    task=f"Handle user request: {text}",
                    expected_output="A helpful response.",
                    stop=False,
                )

        raise ValueError(
            "No routing rule matched the message. Add a rule or register a fallback agent."
        )


class Orchestrator:
    def __init__(
        self,
        registry: AgentRegistry,
        rules: Iterable[RoutingRule],
        *,
        coordinator_name: str = "coordinator",
        summarize_every: int = 12,
        keep_recent_events: int = 20,
        keep_scratchpad: int = 12,
    ):
        self._registry = registry
        self._rules = list(rules)
        self._coordinator_name = coordinator_name

        self._user_history: List[Message] = []
        self._team_conversation: List[TraceEvent] = []
        self._team_events: List[Event] = []

        self._team_memory = TeamMemory(
            summarize_every=summarize_every,
            keep_recent=keep_recent_events,
            keep_scratchpad=keep_scratchpad,
        )

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

        # --- coordinator decision (agent z registry albo fallback DefaultCoordinator) ---
        team_ctx = self.team_context()
        caps = self._registry.list_capabilities()

        coordinator_from_registry = True
        try:
            coordinator_obj = self._registry.get(self._coordinator_name)
        except KeyError:
            coordinator_obj = DefaultCoordinator(self._rules)
            coordinator_from_registry = False

        decide_fn = getattr(coordinator_obj, "decide", None)
        if decide_fn is None or not callable(decide_fn):
            raise TypeError("Coordinator agent must implement decide(...)")

        decision = decide_fn(user_goal=user_msg.content, team_ctx=team_ctx, agents=caps)
        if isinstance(decision, dict):
            decision = CoordinatorDecision.from_dict(decision)
        if not isinstance(decision, CoordinatorDecision):
            raise TypeError("Coordinator must return CoordinatorDecision or dict-compatible JSON")

        decision.validate()

        # decision zawsze idzie do MAS event log (team_events + memory)
        decision_event = Event(
            type="decision",
            actor=getattr(coordinator_obj, "name", self._coordinator_name),
            target=decision.next_agent,
            data=decision.to_dict(),
            timestamp=now_iso(),
            correlation_id=cid,
        )
        self._team_events.append(decision_event)
        self._team_memory.add_event(decision_event)

        # ...ale do legacy team_conversation dopisujemy decision tylko gdy to prawdziwy coordinator z registry
        if coordinator_from_registry:
            self._team_conversation.append(
                TraceEvent(
                    actor=getattr(coordinator_obj, "name", self._coordinator_name),
                    action="decision",
                    target=decision.next_agent,
                    params=decision.to_dict(),
                    outcome="ok",
                    error=None,
                    timestamp=now_iso(),
                    correlation_id=cid,
                )
            )

        if decision.stop:
            reply = Message(
                sender=getattr(coordinator_obj, "name", self._coordinator_name),
                content="OK, kończę.",
                correlation_id=cid,
            )
            self._user_history.append(reply)

            respond_trace = TraceEvent(
                actor=reply.sender,
                action="respond",
                target="user",
                params={"content": reply.content},
                outcome="ok",
                error=None,
                timestamp=now_iso(),
                correlation_id=cid,
            )
            self._team_conversation.append(respond_trace)
            respond_event = respond_trace.to_event()
            self._team_events.append(respond_event)
            self._team_memory.add_event(respond_event)
            return reply

        # --- route ---
        agent = self._registry.get(decision.next_agent)

        route_trace = TraceEvent(
            actor="orchestrator",
            action="route",
            target=getattr(agent, "name", agent.__class__.__name__),
            params={"text": user_msg.content, "task": decision.task},
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
