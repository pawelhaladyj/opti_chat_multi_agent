from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Callable, Mapping

from organizer.core.errors import ToolError
from organizer.core.fixplan import FixPlan
from organizer.core.task import Task


CompletionFn = Callable[[list[dict[str, str]]], str]


@dataclass(frozen=True)
class OpenAIRecoveryTool:
    """
    OpenAIRecoveryTool:
    - bierze ToolError + stack trace + kontekst ostatniego wywołania narzędzia
    - prosi LLM o propozycję naprawy w formie JSON
    - waliduje JSON i mapuje go na FixPlan

    Uwaga: to narzędzie jest opcjonalne.
    Jeśli nie ustawisz OPENAI_API_KEY i nie podasz completion_fn, podniesie RuntimeError.
    """
    name: str = "openai_recovery"
    model: str = "gpt-4o-mini"
    temperature: float = 0.0
    completion_fn: CompletionFn | None = None

    def propose_fix(self, *, error: ToolError, last_task: Task, last_inputs: Mapping[str, Any]) -> FixPlan | None:
        messages = self._build_messages(error=error, last_task=last_task, last_inputs=last_inputs)

        try:
            content = self._complete(messages)
            data = json.loads(content or "{}")
        except Exception:
            return None

        return self._to_fixplan(data=data, last_task=last_task)

    def _complete(self, messages: list[dict[str, str]]) -> str:
        if self.completion_fn is not None:
            return self.completion_fn(messages)

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("Missing env var: OPENAI_API_KEY")

        from openai import OpenAI  # lazy import
        client = OpenAI(api_key=api_key)

        resp = client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            messages=messages,
            response_format={"type": "json_object"},
        )
        return resp.choices[0].message.content or "{}"

    def _build_messages(self, *, error: ToolError, last_task: Task, last_inputs: Mapping[str, Any]) -> list[dict[str, str]]:
        trace = (error.stack_trace or "").strip()
        if len(trace) > 8000:
            trace = trace[-8000:]  # ogon jest najcenniejszy

        schema = (
            "Zwróć WYŁĄCZNIE JSON w jednym z formatów:\n"
            '1) {"action":"retry_tool","tool":"<tool_name>","params":{...},"reason":"..."}\n'
            '2) {"action":"fallback_tool","tool":"<tool_name>","params":{...},"reason":"..."}\n'
            '3) {"action":"fail","tool":null,"params":{},"reason":"..."}\n\n'
            "Zasady:\n"
            "- params to TYLKO patch (zmienione klucze), nie całość\n"
            "- reason krótki i rzeczowy\n"
            "- jeśli sugerujesz retry, domyślnie użyj last_task.target jako tool\n"
        )

        payload = {
            "last_task": {"name": last_task.name, "target": last_task.target},
            "last_inputs": dict(last_inputs),
            "tool_error": {
                "code": error.code,
                "type": error.type,
                "message": error.message,
                "provider": error.provider,
                "request_params": dict(error.request_params),
                "raw_response": error.raw_response,
                "stack_trace_id": error.stack_trace_id,
            },
            "stack_trace_tail": trace,
        }

        return [
            {
                "role": "system",
                "content": (
                    "Jesteś narzędziem diagnostycznym do naprawy parametrów wywołań API (tool-i). "
                    "Masz zaproponować bezpieczną poprawkę parametrów albo fallback. "
                    "Odpowiadaj wyłącznie JSON-em."
                ),
            },
            {"role": "user", "content": schema + "\nKontekst:\n" + json.dumps(payload, ensure_ascii=False)},
        ]

    def _to_fixplan(self, *, data: Any, last_task: Task) -> FixPlan | None:
        if not isinstance(data, dict):
            return None

        action = str(data.get("action") or "").strip()
        tool = data.get("tool", None)
        params = data.get("params") or {}
        reason = str(data.get("reason") or "").strip() or "LLM suggested a fix."

        if not isinstance(params, dict):
            return None

        if action == "retry_tool":
            if not isinstance(tool, str) or not tool.strip():
                return None
            tool = tool.strip()

            # jeśli LLM próbuje zmienić narzędzie w "retry", traktujemy to jak fallback (bez zgadywania)
            if tool != last_task.target:
                return FixPlan(
                    action="fallback_tool",
                    reason=reason,
                    fallback_tool_name=tool,
                    params_patch=params,
                )

            return FixPlan(
                action="retry_with_params",
                reason=reason,
                params_patch=params,
            )

        if action == "fallback_tool":
            if not isinstance(tool, str) or not tool.strip():
                return None
            return FixPlan(
                action="fallback_tool",
                reason=reason,
                fallback_tool_name=tool.strip(),
                params_patch=params,
            )

        if action == "fail":
            return FixPlan(action="fail", reason=reason, params_patch=None)

        return None
