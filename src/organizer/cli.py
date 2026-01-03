from dotenv import load_dotenv
from organizer.core.types import Message
from organizer.core import AgentRegistry, Orchestrator, RoutingRule
from organizer.agents import WeatherAgent, StayAgent, PlannerAgent
from organizer.tools.fake_apis import FakeWeatherAPI, FakeEventsAPI, FakeHousingAPI
from organizer.core.preferences import Preferences
from organizer.tools.real.open_meteo import OpenMeteoWeatherTool
from organizer.core.history_logger import HistoryLogger


def build_orchestrator(*, use_llm: bool = False, use_real_apis: bool = False):
    registry = AgentRegistry()

    # 1) Wybór narzędzi (FAKE vs REAL)
    if use_real_apis:
        from organizer.tools.real.open_meteo import OpenMeteoWeatherTool
        from organizer.tools.real.openai_city_normalizer import OpenAICityNormalizerTool

        weather_tool = OpenMeteoWeatherTool()
        city_normalizer = OpenAICityNormalizerTool()
    else:
        weather_tool = FakeWeatherAPI()
        city_normalizer = None

    events_tool = FakeEventsAPI()   # na razie zawsze fake (stabilne)
    housing_tool = FakeHousingAPI() # na razie zawsze fake (stabilne)

    # 2) Rejestracja agentów z wstrzykniętymi toolami
    registry.register(
        WeatherAgent(
            tool=weather_tool,
            name="weather",
            city_normalizer=city_normalizer,
        )
    )

    registry.register(
        StayAgent(tool=housing_tool, name="stays")
    )

    registry.register(
        PlannerAgent(
            weather_tool=weather_tool,   # <-- ważne: planner używa tego samego źródła pogody
            events_tool=events_tool,
            preferences=Preferences(),
            name="planner",
        )
    )

    # 3) Opcjonalny agent LLM
    if use_llm:
        from organizer.agents.llm import OpenAIAgent
        registry.register(OpenAIAgent())

    # 4) Routing
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
    load_dotenv()
    print("Multi-Agent Organizer (CLI)")
    print("Napisz 'exit' aby zakończyć.\n")

    orch = build_orchestrator(use_llm=True, use_real_apis=True)

    logger = HistoryLogger.create_default()
    print(f"(log) zapisuję historię do: {logger.file_path}\n")

    while True:
        user_input = input("> ").strip()
        if user_input.lower() in {"exit", "quit"}:
            break

        try:
            # 1) zapis usera
            user_msg = Message(sender="user", content=user_input)
            logger.append(user_msg)

            # 2) normalne przetworzenie przez orchestrator
            reply = orch.handle_user_text(user_input)

            # 3) zapis odpowiedzi agenta
            logger.append(reply)

            print(f"\n[{reply.sender}] {reply.content}\n")

        except Exception as e:
            err_msg = Message(sender="error", content=str(e))
            logger.append(err_msg)
            print(f"\n[error] {e}\n")
