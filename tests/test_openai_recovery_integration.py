import os
import pytest

from organizer.core import ToolError, Task
from organizer.tools.real.openai_recovery import OpenAIRecoveryTool


@pytest.mark.integration
def test_openai_recovery_tool_integration_returns_valid_fixplan():
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    tool = OpenAIRecoveryTool()

    err = ToolError(
        code="400",
        type="HTTP_ERROR",
        message="invalid date format",
        provider="some_api",
        request_params={"date": "2026/01/03"},
        raw_response="Bad Request",
        stack_trace_id="int001",
        stack_trace="Traceback (most recent call last): ValueError: ...",
    )

    task = Task(name="events_search", target="some_api", inputs={"date": "2026/01/03", "city": "Kraków"})

    plan = tool.propose_fix(error=err, last_task=task, last_inputs=task.inputs)
    assert plan is not None
    assert plan.action in {"retry_with_params", "fallback_tool", "fail"}
