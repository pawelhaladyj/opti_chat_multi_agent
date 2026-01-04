from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path

from organizer.core.types import Message
from organizer.core import AgentRegistry, Orchestrator, RoutingRule
from organizer.agents import WeatherAgent, StayAgent, PlannerAgent
from organizer.tools.fake_apis import FakeWeatherAPI, FakeEventsAPI, FakeHousingAPI
from organizer.core.history_logger import HistoryLogger
from organizer.core.trace_logger import write_trace_jsonl


def build_orchestrator(*, use_llm: bool = False, use_real_apis: bool = False):
    registry = AgentRegistry()

    # 1) Wybór narzędzi (FAKE vs REAL)
    if use_real_apis:
        from organizer.tools.real.open_meteo import OpenMeteoWeatherTool
        weather_tool = OpenMeteoWeatherTool()
    else:
        weather_tool = FakeWeatherAPI()

    events_tool = FakeEventsAPI()
    housing_tool = FakeHousingAPI()

    # 2) Agenci
    registry.register(WeatherAgent(tool=weather_tool))
    registry.register(StayAgent(tool=housing_tool))

    # FIX: PlannerAgent wymaga keyword-only: events_tool ORAZ weather_tool
    registry.register(
        PlannerAgent(
            events_tool=events_tool,
            weather_tool=weather_tool,
        )
    )

    # 3) Routing rules
    rules = [
        RoutingRule("pogoda", "weather"),
        RoutingRule("nocleg", "stays"),
        RoutingRule("plan", "planner"),
        RoutingRule("zaplanuj", "planner"),
    ]

    return Orchestrator(registry, rules)


def run_cli():
    load_dotenv()
    print("Multi-Agent Organizer (CLI)")
    print("Napisz 'exit' aby zakończyć.\n")

    orch = build_orchestrator(use_llm=True, use_real_apis=True)

    logger = HistoryLogger.create_default()
    print(f"(log) zapisuję historię do: {logger.file_path}\n")

    trace_path = Path(logger.file_path).with_name(
        f"trace_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
    )

    while True:
        user_input = input("> ").strip()
        if user_input.lower() in {"exit", "quit"}:
            break

        try:
            user_msg = Message(sender="user", content=user_input)
            logger.append(user_msg)

            reply = orch.handle_user_text(user_input)
            logger.append(reply)

            write_trace_jsonl(orch.team_conversation, trace_path)

            print(f"\n[{reply.sender}] {reply.content}\n")

        except Exception as e:
            err_msg = Message(sender="error", content=str(e))
            logger.append(err_msg)
            print(f"\n[error] {e}\n")
