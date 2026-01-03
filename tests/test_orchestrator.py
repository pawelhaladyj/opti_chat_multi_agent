import pytest

from organizer.core import AgentRegistry, Orchestrator, RoutingRule
from organizer.agents import WeatherAgent, StayAgent
from organizer.tools import FakeWeatherAPI, FakeHousingAPI


def make_orchestrator() -> Orchestrator:
    registry = AgentRegistry()
    registry.register(WeatherAgent(tool=FakeWeatherAPI(), name="weather"))
    registry.register(StayAgent(tool=FakeHousingAPI(), name="stays"))

    rules = [
        RoutingRule(keyword="pogoda", agent_name="weather"),
        RoutingRule(keyword="weather", agent_name="weather"),
        RoutingRule(keyword="nocleg", agent_name="stays"),
        RoutingRule(keyword="hotel", agent_name="stays"),
    ]
    return Orchestrator(registry=registry, rules=rules)


def test_weather_question_routes_to_weather_agent():
    orch = make_orchestrator()
    reply = orch.handle_user_text("Jaka będzie pogoda jutro w Warszawie?")

    assert reply.sender == "weather"
    assert "pogod" in reply.content.lower() or "stub" in reply.content.lower()


def test_stay_question_routes_to_stay_agent():
    orch = make_orchestrator()
    reply = orch.handle_user_text("Znajdź nocleg w Krakowie na weekend")

    assert reply.sender == "stays"
    assert "nocleg" in reply.content.lower() or "stub" in reply.content.lower()


def test_history_is_saved_user_then_agent():
    orch = make_orchestrator()
    orch.handle_user_text("Jaka będzie pogoda jutro?")

    history = orch.history
    assert len(history) == 2
    assert history[0].sender == "user"
    assert history[1].sender == "weather"


def test_no_matching_rule_raises():
    orch = make_orchestrator()
    with pytest.raises(ValueError):
        orch.handle_user_text("Opowiedz mi o filozofii Kanta")
