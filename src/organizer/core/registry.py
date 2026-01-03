from typing import Dict
from organizer.core.agent import Agent


class AgentRegistry:
    """
    Rejestr agentów dostępnych w systemie.
    """

    def __init__(self):
        self._agents: Dict[str, Agent] = {}

    def register(self, agent: Agent) -> None:
        if agent.name in self._agents:
            raise ValueError(f"Agent '{agent.name}' is already registered")

        self._agents[agent.name] = agent

    def get(self, name: str) -> Agent:
        try:
            return self._agents[name]
        except KeyError:
            raise KeyError(f"Agent '{name}' not found")

    def list_names(self) -> list[str]:
        return list(self._agents.keys())
