from organizer.agents import RecoveryAgent
from organizer.core import ToolError, Task


def test_no_results_suggests_language_and_count_patch():
    agent = RecoveryAgent()

    err = ToolError(
        code="EXCEPTION",
        type="EXCEPTION",
        message="Open-Meteo geocoding: no results for 'Warszawie'",
        provider="open_meteo_geocoding",
        request_params={"location": "Warszawie", "count": 1, "language": "en"},
        raw_response=None,
        stack_trace_id="abc123",
    )

    task = Task(
        name="weather_lookup",
        target="open_meteo_geocoding",
        inputs={"location": "Warszawie", "count": 1, "language": "en"},
    )

    plan = agent.propose_fix(error=err, last_task=task, last_inputs=task.inputs)

    assert plan.action == "retry_with_params"
    assert plan.params_patch["language"] == "pl"
    assert plan.params_patch["count"] >= 5


def test_http400_invalid_date_format_suggests_iso_date():
    agent = RecoveryAgent()

    err = ToolError(
        code="400",
        type="HTTP_ERROR",
        message="invalid date format",
        provider="some_api",
        request_params={"date": "2026/01/03"},
        raw_response="Bad Request",
        stack_trace_id="def456",
    )

    task = Task(
        name="events_search",
        target="some_api",
        inputs={"date": "2026/01/03", "city": "Kraków"},
    )

    plan = agent.propose_fix(error=err, last_task=task, last_inputs=task.inputs)

    assert plan.action == "retry_with_params"
    assert plan.params_patch["date"] == "2026-01-03"
