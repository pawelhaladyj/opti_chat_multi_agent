import pytest

from organizer.core import RetryPolicy, call_tool_with_retry, RetryExceededError


def test_tool_succeeds_after_two_failures():
    calls = {"n": 0}

    def flaky_tool(**kwargs):
        calls["n"] += 1
        if calls["n"] <= 2:
            raise ValueError("temporary failure")
        return {"ok": True, "attempt": calls["n"]}

    policy = RetryPolicy(max_attempts=5, backoff_seconds=0.0)

    result, traces = call_tool_with_retry(
        tool_name="flaky_tool",
        tool_callable=flaky_tool,
        params={"x": 1},
        actor="tool_runner",
        correlation_id="cid-retry-1",
        policy=policy,
    )

    assert result["ok"] is True
    assert calls["n"] == 3  # 2 fail + 1 success
    assert len(traces) == 3
    assert traces[0].outcome == "error"
    assert traces[1].outcome == "error"
    assert traces[2].outcome == "success"


def test_retry_exceeded_raises_controlled_error():
    def always_bad_tool(**kwargs):
        raise ValueError("always fails")

    policy = RetryPolicy(max_attempts=3, backoff_seconds=0.0)

    with pytest.raises(RetryExceededError) as excinfo:
        call_tool_with_retry(
            tool_name="always_bad",
            tool_callable=always_bad_tool,
            params={"x": 1},
            actor="tool_runner",
            correlation_id="cid-retry-2",
            policy=policy,
        )

    err = excinfo.value
    assert "Retry exceeded" in str(err)
    assert err.last_error is not None
    assert "always fails" in err.last_error.message
