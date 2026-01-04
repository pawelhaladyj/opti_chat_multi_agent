from organizer.core import AgentRegistry, Orchestrator, RoutingRule
from organizer.core.agent import Agent
from organizer.core.types import Message


class EchoAgent(Agent):
    def __init__(self):
        super().__init__(name="echo")

    def handle(self, message: Message) -> Message:
        return Message(sender=self.name, content=f"echo: {message.content}")


def test_orchestrator_records_team_conversation_route_and_respond():
    registry = AgentRegistry()
    registry.register(EchoAgent())

    orch = Orchestrator(registry, [RoutingRule("echo", "echo")])

    reply = orch.handle_user_text("echo test")

    assert reply.sender == "echo"
    trace = orch.team_conversation
    assert len(trace) == 2

    assert trace[0].action == "route"
    assert trace[0].target == "echo"

    assert trace[1].action == "respond"
    assert trace[1].actor == "echo"
