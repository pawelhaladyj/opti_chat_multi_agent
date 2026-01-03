import pytest
from organizer.core import Agent, AgentRegistry, Message


class DummyAgent(Agent):
    def handle(self, message: Message) -> Message:
        return Message(sender=self.name, content="ok")


def test_agent_can_be_registered():
    registry = AgentRegistry()
    agent = DummyAgent(name="dummy")

    registry.register(agent)

    assert "dummy" in registry.list_names()


def test_registry_returns_agent_by_name():
    registry = AgentRegistry()
    agent = DummyAgent(name="dummy")

    registry.register(agent)
    retrieved = registry.get("dummy")

    assert retrieved is agent


def test_registry_rejects_duplicate_agent_names():
    registry = AgentRegistry()
    agent1 = DummyAgent(name="dummy")
    agent2 = DummyAgent(name="dummy")

    registry.register(agent1)

    with pytest.raises(ValueError):
        registry.register(agent2)
