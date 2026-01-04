from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, List, Tuple
import uuid

from organizer.core.registry import AgentRegistry
from organizer.core.types import Message
from organizer.core.agent import Agent
from organizer.core.trace import TraceEvent


@dataclass(frozen=True)
class RoutingRule:
    keyword: str
    agent_name: str


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Orchestrator:
    """
    Orchestrator (new_design)

    Kompatybilność:
    - zachowuje `handle(message: Message)` oraz `history` (wymagane przez testy)
    - dodaje `team_conversation` (TraceEvent) jako fundament iteracji 13 kontraktu MAS
    """

    def __init__(self, registry: AgentRegistry, rules: Iterable[RoutingRule]):
        self._registry = registry
        self._rules = list(rules)

        # Historia rozmowy user<->agent (to, co testy nazywają orch.history)
        self._history: List[Message] = []

        # Wewnętrzny trace zespołu (team_conversation)
        self._team_conversation: List[TraceEvent] = []

    @property
    def history(self) -> Tuple[Message, ...]:
        return tuple(self._history)

    @property
    def team_conversation(self) -> Tuple[TraceEvent, ...]:
        return tuple(self._team_conversation)

    def reset(self) -> None:
        """
        Resetuje stan sesji (historia + trace).
        """
        self._history.clear()
        self._team_conversation.clear()

    def handle(self, message: Message) -> Message:
        """
        Single-step obsługa wiadomości.
        Zapisuje:
        - orch.history: user msg, agent reply
        - orch.team_conversation: route, respond
        """
        cid = f"CID-{uuid.uuid4().hex[:12]}"

        # historia: user
        self._history.append(message)

        agent = self._pick_agent(message)

        # trace: routing
        self._team_conversation.append(
            TraceEvent(
                actor="orchestrator",
                action="route",
                target=getattr(agent, "name", agent.__class__.__name__),
                params={"text": message.content},
                outcome="ok",
                error=None,
                timestamp=_now_iso(),
                correlation_id=cid,
            )
        )

        reply = agent.handle(message)

        # historia: agent
        self._history.append(reply)

        # trace: odpowiedź agenta
        self._team_conversation.append(
            TraceEvent(
                actor=getattr(agent, "name", agent.__class__.__name__),
                action="respond",
                target="user",
                params={"content": reply.content},
                outcome="ok",
                error=None,
                timestamp=_now_iso(),
                correlation_id=cid,
            )
        )

        return reply

    def handle_user_text(self, user_text: str) -> Message:
        return self.handle(Message(sender="user", content=user_text))

    def _pick_agent(self, message: Message) -> Agent:
        content = (message.content or "").lower()
        for rule in self._rules:
            if rule.keyword.lower() in content:
                return self._registry.get(rule.agent_name)

        raise ValueError(
            "No routing rule matched the message. "
            "Add a rule or register a fallback agent."
        )
