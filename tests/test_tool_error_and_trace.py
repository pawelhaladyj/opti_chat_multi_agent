from organizer.core import ToolError, TraceEvent, call_tool_with_trace


def test_wrap_exception_into_toolerror_and_trace():
    def bad_tool(**kwargs):
        raise ValueError("no results for 'Warszawie'")

    result, trace = call_tool_with_trace(
        tool_name="open_meteo_geocoding",
        tool_callable=bad_tool,
        params={"location": "Warszawie", "count": 1, "language": "en"},
        actor="weather_agent",
        correlation_id="cid-1",
    )

    assert result is None
    assert isinstance(trace, TraceEvent)
    assert trace.actor == "weather_agent"
    assert trace.target == "open_meteo_geocoding"
    assert trace.params["location"] == "Warszawie"
    assert trace.outcome == "error"
    assert isinstance(trace.error, ToolError)
    assert trace.error.provider == "open_meteo_geocoding"
    assert trace.error.code == "EXCEPTION"
    assert "Warszawie" in trace.error.message
    assert trace.error.stack_trace_id  # niepuste


def test_trace_contains_params_and_tool_name_on_success():
    def ok_tool(**kwargs):
        return {"ok": True, "echo": dict(kwargs)}

    result, trace = call_tool_with_trace(
        tool_name="fake_weather_api",
        tool_callable=ok_tool,
        params={"location": "Kraków", "date": "tomorrow"},
        actor="weather_agent",
        correlation_id="cid-2",
    )

    assert result["ok"] is True
    assert trace.outcome == "success"
    assert trace.target == "fake_weather_api"
    assert trace.params["location"] == "Kraków"
    assert trace.error is None
