from organizer.core import AgentRegistry, Orchestrator, RoutingRule
from organizer.core.agent import Agent
from organizer.core.types import Message


class EchoAgent(Agent):
    def __init__(self):
        super().__init__(name="echo")

    def handle(self, message: Message) -> Message:
        return Message(sender="echo", content=f"echo: {message.content}")


def test_orchestrator_keeps_user_history_separately_and_history_alias_works():
    reg = AgentRegistry()
    reg.register(EchoAgent())
    orch = Orchestrator(reg, [RoutingRule("echo", "echo")], summarize_every=2)

    orch.handle_user_text("echo test")

    assert len(orch.user_history) == 2  # user + agent
    assert orch.history == orch.user_history  # kompatybilność
    assert len(orch.team_events) >= 2  # route + respond
    # po 2 eventach rolling summary powinno powstać
    ctx = orch.team_context()
    assert ctx.rolling_summary != ""
