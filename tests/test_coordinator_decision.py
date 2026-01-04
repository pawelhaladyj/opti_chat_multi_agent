import pytest
from organizer.core.decision import CoordinatorDecision


def test_decision_roundtrip_json():
    d1 = CoordinatorDecision(
        next_agent="weather",
        task="Get forecast",
        expected_output="Short forecast",
        stop=False,
        needed_tools=["weather_tool"],
    )
    raw = d1.to_dict()
    d2 = CoordinatorDecision.from_dict(raw)
    assert d2.next_agent == "weather"
    assert d2.needed_tools == ["weather_tool"]
    d2.validate()


def test_decision_validate_rejects_empty_fields():
    with pytest.raises(ValueError):
        CoordinatorDecision(next_agent="", task="t", expected_output="e").validate()
