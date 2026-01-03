from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping

from organizer.core.errors import ToolError
from organizer.core.fixplan import FixPlan
from organizer.core.task import Task
from organizer.tools.real.openai_recovery import OpenAIRecoveryTool


@dataclass(frozen=True)
class RecoveryAgent:
    """
    RecoveryAgent v2:

    1) Najpierw heurystyki (v1) — szybkie, przewidywalne, bez LLM.
    2) Jeśli heurystyki nie mają sensownej poprawki (fail) albo idą w ogólny fallback,
       wtedy (opcjonalnie) odpalamy LLM-diagnosis przez OpenAIRecoveryTool.
    """
    name: str = "recovery"
    llm_recovery_tool: OpenAIRecoveryTool | None = None

    def propose_fix(self, *, error: ToolError, last_task: Task, last_inputs: Mapping[str, Any]) -> FixPlan:
        # 1) Typowe przypadki "no results" (np. geocoding)
        if self._looks_like_no_results(error):
            patch: dict[str, Any] = {}

            if "language" in last_inputs and last_inputs.get("language") != "pl":
                patch["language"] = "pl"

            if "count" in last_inputs:
                try:
                    patch["count"] = max(int(last_inputs.get("count") or 1), 5)
                except Exception:
                    patch["count"] = 5

            if patch:
                return FixPlan(
                    action="retry_with_params",
                    reason="Tool returned no results; try broader query (language/count).",
                    params_patch=patch,
                )

            plan = FixPlan(
                action="fallback_tool",
                reason="Tool returned no results; try fallback geocoder provider.",
                fallback_tool_name="fallback_geocoder",
                params_patch=dict(last_inputs),
            )
            return self._maybe_llm(plan=plan, error=error, last_task=last_task, last_inputs=last_inputs)

        # 2) Błędy formatu (np. data)
        if error.code == "400" or self._looks_like_invalid_date(error):
            patch = self._fix_date_format_patch(last_inputs)
            if patch:
                return FixPlan(
                    action="retry_with_params",
                    reason="Bad request likely due to invalid date format; normalize to YYYY-MM-DD.",
                    params_patch=patch,
                )

        # 3) Timeout / transient -> retry same
        if error.type in {"TIMEOUT"} or self._looks_like_transient(error):
            return FixPlan(
                action="retry_same",
                reason="Transient error; safe to retry.",
                params_patch=None,
            )

        # 4) Domyślnie: heurystyki nie wiedzą -> LLM (jeśli włączone)
        plan = FixPlan(
            action="fail",
            reason="No heuristic fix available for this tool error.",
            params_patch=None,
        )
        return self._maybe_llm(plan=plan, error=error, last_task=last_task, last_inputs=last_inputs)

    def _maybe_llm(self, *, plan: FixPlan, error: ToolError, last_task: Task, last_inputs: Mapping[str, Any]) -> FixPlan:
        if plan.action not in {"fail", "fallback_tool"}:
            return plan
        if self.llm_recovery_tool is None:
            return plan

        try:
            llm_plan = self.llm_recovery_tool.propose_fix(
                error=error,
                last_task=last_task,
                last_inputs=last_inputs,
            )
        except Exception:
            # Recovery nie może wysadzić głównego flow
            return plan

        if llm_plan is None or llm_plan.action == "fail":
            return plan

        return llm_plan

    def _looks_like_no_results(self, error: ToolError) -> bool:
        msg = (error.message or "").lower()
        return ("no results" in msg) or ("not found" in msg) or ("no result" in msg)

    def _looks_like_invalid_date(self, error: ToolError) -> bool:
        msg = (error.message or "").lower()
        return ("invalid date" in msg) or ("date format" in msg) or ("fromisoformat" in msg)

    def _fix_date_format_patch(self, inputs: Mapping[str, Any]) -> dict[str, Any]:
        if "date" not in inputs:
            return {}

        raw = str(inputs.get("date") or "").strip()
        if not raw:
            return {}

        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
            return {}

        m = re.fullmatch(r"(\d{4})[\/\.](\d{2})[\/\.](\d{2})", raw)
        if m:
            y, mo, d = m.group(1), m.group(2), m.group(3)
            return {"date": f"{y}-{mo}-{d}"}

        m = re.fullmatch(r"(\d{2})-(\d{2})-(\d{4})", raw)
        if m:
            d, mo, y = m.group(1), m.group(2), m.group(3)
            return {"date": f"{y}-{mo}-{d}"}

        return {}

    def _looks_like_transient(self, error: ToolError) -> bool:
        msg = (error.message or "").lower()
        return any(x in msg for x in ["temporar", "timeout", "try again", "rate limit", "too many requests"])
