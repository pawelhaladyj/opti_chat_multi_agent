from organizer.core.types import Event
from organizer.core.replay import replay_history_from_events


def test_replay_reconstructs_agent_messages_from_respond_events():
    events = [
        Event(type="route", actor="orchestrator", target="weather", data={"text": "pogoda"}),
        Event(type="respond", actor="weather", target="user", data={"content": "OK pogoda"}, correlation_id="CID-10"),
        Event(type="respond", actor="planner", target="user", data={"content": "OK plan"}, correlation_id="CID-10"),
    ]

    history = replay_history_from_events(events)
    assert len(history) == 2
    assert history[0].sender == "weather"
    assert history[0].content == "OK pogoda"
    assert history[0].meta.get("replayed") is True
    assert history[1].sender == "planner"
