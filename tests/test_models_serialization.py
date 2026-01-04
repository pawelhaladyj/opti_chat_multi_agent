from organizer.core.types import Message, Event, AgentResult, ToolResult

def test_message_roundtrip_dict():
    m1 = Message(sender="user", content="hello", meta={"x": 1}, correlation_id="CID-1")
    d = m1.to_dict()
    m2 = Message.from_dict(d)
    assert m2.sender == "user"
    assert m2.content == "hello"
    assert m2.role == "user"
    assert m2.meta["x"] == 1
    assert m2.correlation_id == "CID-1"


def test_event_roundtrip_dict():
    e1 = Event(type="tool_call", actor="tool_runner", target="open_meteo", data={"q": "Warszawa"}, correlation_id="CID-2")
    d = e1.to_dict()
    e2 = Event.from_dict(d)
    assert e2.type == "tool_call"
    assert e2.actor == "tool_runner"
    assert e2.target == "open_meteo"
    assert e2.data["q"] == "Warszawa"
    assert e2.correlation_id == "CID-2"


def test_agentresult_roundtrip_dict():
    msg = Message(sender="planner", content="plan", meta={"mode": "fast"}, correlation_id="CID-3")
    ev = Event(type="decision", actor="coordinator", target="planner", data={"task": "make plan"}, correlation_id="CID-3")
    r1 = AgentResult(message=msg, payload={"steps": [1, 2]}, events=[ev])

    d = r1.to_dict()
    r2 = AgentResult.from_dict(d)

    assert r2.message.sender == "planner"
    assert r2.payload["steps"] == [1, 2]
    assert len(r2.events) == 1
    assert r2.events[0].type == "decision"

def test_toolresult_roundtrip_dict():
    r1 = ToolResult(ok=True, data={"temp": 12}, meta={"source": "fake"}, correlation_id="CID-T1")
    d = r1.to_dict()
    r2 = ToolResult.from_dict(d)
    assert r2.ok is True
    assert r2.data["temp"] == 12
    assert r2.meta["source"] == "fake"
    assert r2.correlation_id == "CID-T1"
