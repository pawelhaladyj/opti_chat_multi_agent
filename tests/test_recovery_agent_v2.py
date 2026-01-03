import json

from organizer.agents import RecoveryAgent
from organizer.core import ToolError, Task
from organizer.tools.real.openai_recovery import OpenAIRecoveryTool


def test_recovery_agent_v2_uses_llm_when_heuristics_fail():
    # Stub: udaje LLM, zwraca poprawkę jako JSON
    def stub_completion(_messages):
        return json.dumps(
            {
                "action": "retry_tool",
                "tool": "some_api",
                "params": {"date": "2026-01-03"},
                "reason": "Normalize date to ISO 8601.",
            }
        )

    llm_tool = OpenAIRecoveryTool(completion_fn=stub_completion)
    agent = RecoveryAgent(llm_recovery_tool=llm_tool)

    # Taki błąd nie odpala heurystyk date/no_results/timeout -> LLM powinien wejść
    err = ToolError(
        code="422",
        type="HTTP_ERROR",
        message="schema validation error",
        provider="some_api",
        request_params={"date": "2026/01/03"},
        raw_response="Unprocessable Entity",
        stack_trace_id="v2abc",
        stack_trace="Traceback (most recent call last): ...",
    )

    task = Task(
        name="events_search",
        target="some_api",
        inputs={"date": "2026/01/03", "city": "Kraków"},
    )

    plan = agent.propose_fix(error=err, last_task=task, last_inputs=task.inputs)

    assert plan.action == "retry_with_params"
    assert plan.params_patch["date"] == "2026-01-03"


def test_openai_recovery_tool_maps_fallback_tool():
    def stub_completion(_messages):
        return json.dumps(
            {
                "action": "fallback_tool",
                "tool": "fallback_geocoder",
                "params": {"language": "pl"},
                "reason": "Switch provider.",
            }
        )

    llm_tool = OpenAIRecoveryTool(completion_fn=stub_completion)

    err = ToolError(
        code="EXCEPTION",
        type="EXCEPTION",
        message="unexpected error",
        provider="open_meteo_geocoding",
        request_params={"location": "Warszawie", "language": "en"},
        raw_response=None,
        stack_trace_id="v2def",
        stack_trace="Traceback (most recent call last): ...",
    )

    task = Task(
        name="weather_lookup",
        target="open_meteo_geocoding",
        inputs={"location": "Warszawie", "language": "en"},
    )

    plan = llm_tool.propose_fix(error=err, last_task=task, last_inputs=task.inputs)
    assert plan is not None
    assert plan.action == "fallback_tool"
    assert plan.fallback_tool_name == "fallback_geocoder"
    assert plan.params_patch["language"] == "pl"
