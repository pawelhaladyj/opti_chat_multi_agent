from organizer.core import AgentRegistry, Orchestrator, RoutingRule
from organizer.agents import WeatherAgent, StayAgent, PlannerAgent
from organizer.tools.fake_apis import FakeWeatherAPI, FakeEventsAPI, FakeHousingAPI
from organizer.core.preferences import Preferences
from organizer.tools.real.open_meteo import OpenMeteoWeatherTool


def build_orchestrator(use_llm: bool = False):
    registry = AgentRegistry()

    registry.register(
        WeatherAgent(tool=OpenMeteoWeatherTool(), name="weather")
    )
    registry.register(
        StayAgent(tool=FakeHousingAPI(), name="stays")
    )
    registry.register(
        PlannerAgent(
            weather_tool=FakeWeatherAPI(),
            events_tool=FakeEventsAPI(),
            preferences=Preferences(),
            name="planner",
        )
    )

    if use_llm:
        from organizer.agents.llm import OpenAIAgent
        registry.register(OpenAIAgent())

    rules = [
        RoutingRule("pogoda", "weather"),
        RoutingRule("nocleg", "stays"),
        RoutingRule("plan", "planner"),
        RoutingRule("zaplanuj", "planner"),
    ]

    if use_llm:
        rules.append(RoutingRule("dlaczego", "llm"))
        rules.append(RoutingRule("opowiedz", "llm"))

    return Orchestrator(registry, rules)


def run_cli():
    print("Multi-Agent Organizer (CLI)")
    print("Napisz 'exit' aby zakończyć.\n")

    orch = build_orchestrator(use_llm=True)

    while True:
        user_input = input("> ").strip()
        if user_input.lower() in {"exit", "quit"}:
            break

        try:
            reply = orch.handle_user_text(user_input)
            print(f"\n[{reply.sender}] {reply.content}\n")
        except Exception as e:
            print(f"\n[error] {e}\n")
