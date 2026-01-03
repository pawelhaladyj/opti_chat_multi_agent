from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from organizer.core.registry import AgentRegistry
from organizer.core.types import Message
from organizer.core.agent import Agent


@dataclass(frozen=True)
class RoutingRule:
    """
    Prosta reguła routingu: jeśli keyword występuje w treści,
    to kierujemy wiadomość do agenta o danej nazwie.
    """
    keyword: str
    agent_name: str


class Orchestrator:
    """
    Dyspozytor: bierze wiadomość usera, wybiera agenta,
    zbiera odpowiedź i zapisuje historię rozmowy.
    """

    def __init__(self, registry: AgentRegistry, rules: Iterable[RoutingRule]):
        self._registry = registry
        self._rules = list(rules)
        self._history: list[Message] = []

    @property
    def history(self) -> list[Message]:
        # Zwracamy kopię, żeby nikt z zewnątrz nie psuł historii
        return list(self._history)

    def handle_user_text(self, text: str) -> Message:
        user_msg = Message(sender="user", content=text)
        self._history.append(user_msg)

        agent = self._pick_agent(user_msg)
        agent_reply = agent.handle(user_msg)

        self._history.append(agent_reply)
        return agent_reply

    def _pick_agent(self, message: Message) -> Agent:
        content = message.content.lower()

        for rule in self._rules:
            if rule.keyword.lower() in content:
                return self._registry.get(rule.agent_name)

        raise ValueError(
            "No routing rule matched the message. "
            "Add a rule or register a fallback agent."
        )
