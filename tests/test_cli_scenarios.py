from organizer.cli import build_orchestrator


def test_weather_conversation_script():
    orch = build_orchestrator(use_llm=False)

    reply = orch.handle_user_text("Jaka będzie pogoda w Warszawa?")
    assert reply.sender == "weather"
    assert "°C" in reply.content


def test_planner_conversation_script():
    orch = build_orchestrator(use_llm=False)

    reply = orch.handle_user_text("Zaplanuj mi dzień w Krakowie")
    assert reply.sender == "planner"
    assert "Plan dla" in reply.content


def test_stays_conversation_script():
    orch = build_orchestrator(use_llm=False)

    reply = orch.handle_user_text("Znajdź nocleg w Gdańsku")
    assert reply.sender == "stays"
    assert "nocleg" in reply.content.lower() or "pln" in reply.content.lower()
