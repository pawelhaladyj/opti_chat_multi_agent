from __future__ import annotations

from typing import Dict, List
from organizer.core.agent import Agent
from organizer.core.capabilities import AgentCapability


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: Dict[str, Agent] = {}

    def register(self, agent: Agent) -> None:
        # testy oczekują ValueError przy duplikacie
        if agent.name in self._agents:
            raise ValueError(f"Agent with name '{agent.name}' is already registered")
        self._agents[agent.name] = agent

    def get(self, name: str) -> Agent:
        return self._agents[name]

    def list_names(self) -> List[str]:
        # testy oczekują istnienia list_names()
        return list(self._agents.keys())

    def list_capabilities(self) -> List[AgentCapability]:
        caps: List[AgentCapability] = []
        for name, agent in self._agents.items():
            desc = getattr(agent, "description", "") or agent.__class__.__doc__ or ""
            caps.append(AgentCapability(name=name, description=(desc or "").strip()))
        return caps
