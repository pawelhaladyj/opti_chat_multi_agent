from __future__ import annotations

import hashlib
import traceback
import uuid
from typing import Any, Mapping

from organizer.core.errors import ToolError
from organizer.core.trace import TraceEvent


def _stack_trace_id(tb: str) -> str:
    # krótki, stabilny identyfikator treści stack trace
    return hashlib.sha256(tb.encode("utf-8")).hexdigest()[:12]


def _make_tool_error(
    *,
    provider: str,
    request_params: Mapping[str, Any],
    exc: Exception,
) -> ToolError:
    tb = traceback.format_exc()
    stid = _stack_trace_id(tb)

    # Bez zależności od konkretnego HTTP klienta:
    # jeśli kiedyś dodasz httpx/requests wyjątki — rozszerzymy mapowanie.
    code = "EXCEPTION"
    err_type = "EXCEPTION"
    message = str(exc).strip() or exc.__class__.__name__

    raw_response = None
    # Tu w przyszłości łatwo dołożysz: http status, response body itp.

    return ToolError(
        code=code,
        type=err_type,
        message=message,
        provider=provider,
        request_params=request_params,
        raw_response=raw_response,
        stack_trace_id=stid,
    )


def call_tool_with_trace(
    *,
    tool_name: str,
    tool_callable: Any,
    params: Mapping[str, Any],
    actor: str = "tool_runner",
    correlation_id: str | None = None,
) -> tuple[Any | None, TraceEvent]:
    """
    Wywołuje narzędzie i ZAWSZE zwraca TraceEvent.
    - w sukcesie: (result, TraceEvent(outcome="success", error=None))
    - w błędzie:  (None, TraceEvent(outcome="error", error=ToolError))
    """
    cid = correlation_id or uuid.uuid4().hex

    try:
        result = tool_callable(**dict(params))
        trace = TraceEvent(
            actor=actor,
            action="tool_call",
            target=tool_name,
            params=dict(params),
            outcome="success",
            error=None,
            timestamp=TraceEvent.now_iso(),
            correlation_id=cid,
        )
        return result, trace

    except Exception as exc:  # celowo szeroko: chcemy ustandaryzować wszystko
        terr = _make_tool_error(provider=tool_name, request_params=params, exc=exc)
        trace = TraceEvent(
            actor=actor,
            action="tool_call",
            target=tool_name,
            params=dict(params),
            outcome="error",
            error=terr,
            timestamp=TraceEvent.now_iso(),
            correlation_id=cid,
        )
        return None, trace
