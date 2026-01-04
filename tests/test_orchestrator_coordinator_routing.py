from organizer.core import AgentRegistry, Orchestrator, RoutingRule
from organizer.core.agent import Agent
from organizer.core.types import Message
from organizer.agents.coordinator import CoordinatorAgent


class EchoAgent(Agent):
    def __init__(self, name: str):
        super().__init__(name=name)

    def handle(self, message: Message) -> Message:
        return Message(sender=self.name, content=f"{self.name}: {message.content}")


def test_orchestrator_uses_coordinator_decision_and_records_decision_in_trace():
    reg = AgentRegistry()
    reg.register(CoordinatorAgent(name="coordinator"))
    reg.register(EchoAgent("weather"))
    reg.register(EchoAgent("planner"))
    reg.register(EchoAgent("stays"))

    orch = Orchestrator(reg, [RoutingRule("legacy", "weather")], coordinator_name="coordinator")

    reply = orch.handle_user_text("czy będzie wiało w Bydgoszczy?")

    # Coordinator powinien rozpoznać wiatr -> weather
    assert reply.sender == "weather"

    trace = orch.team_conversation
    # decision + route + respond = minimum 3
    assert len(trace) >= 3
    assert trace[0].action == "decision"
    assert trace[0].params["next_agent"] == "weather"
    assert trace[1].action == "route"
    assert trace[-1].action == "respond"
