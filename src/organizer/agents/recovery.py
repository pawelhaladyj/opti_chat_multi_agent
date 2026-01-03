from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping

from organizer.core.errors import ToolError
from organizer.core.fixplan import FixPlan
from organizer.core.task import Task


@dataclass(frozen=True)
class RecoveryAgent:
    """
    RecoveryAgent v1:
    - bez LLM
    - heurystyki oparte o typ błędu + kontekst wywołania
    - nie "zna domeny" (miast), ale naprawia formaty i parametry requestów
    """
    name: str = "recovery"

    def propose_fix(self, *, error: ToolError, last_task: Task, last_inputs: Mapping[str, Any]) -> FixPlan:
        # 1) Typowe przypadki "no results" (np. geocoding)
        if self._looks_like_no_results(error):
            patch: dict[str, Any] = {}

            # często pomaga:
            # - language="pl" (jeśli user pisze po polsku)
            # - count zwiększyć
            if "language" in last_inputs and last_inputs.get("language") != "pl":
                patch["language"] = "pl"

            if "count" in last_inputs:
                patch["count"] = max(int(last_inputs.get("count") or 1), 5)

            # jeśli nic nie umiemy poprawić parametrami, zasugeruj fallback tool
            if patch:
                return FixPlan(
                    action="retry_with_params",
                    reason="Tool returned no results; try broader query (language/count).",
                    params_patch=patch,
                )
            return FixPlan(
                action="fallback_tool",
                reason="Tool returned no results; try fallback geocoder provider.",
                fallback_tool_name="fallback_geocoder",
                params_patch=dict(last_inputs),
            )

        # 2) HTTP 400: często format parametrów (np. date)
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

        # 4) Domyślnie: nie wiemy
        return FixPlan(
            action="fail",
            reason="No safe heuristic fix found for this error.",
            params_patch=None,
        )

    def _looks_like_no_results(self, error: ToolError) -> bool:
        msg = (error.message or "").lower()
        return ("no results" in msg) or ("not found" in msg) or ("no result" in msg)

    def _looks_like_invalid_date(self, error: ToolError) -> bool:
        msg = (error.message or "").lower()
        return ("invalid date" in msg) or ("date format" in msg) or ("fromisoformat" in msg)

    def _fix_date_format_patch(self, inputs: Mapping[str, Any]) -> dict[str, Any]:
        """
        Jeśli w inputs jest date i wygląda podejrzanie, spróbuj ją sprowadzić do YYYY-MM-DD.
        Nie zgadujemy daty — tylko normalizujemy format, jeśli to możliwe.
        """
        if "date" not in inputs:
            return {}

        raw = str(inputs.get("date") or "").strip()
        if not raw:
            return {}

        # jeżeli już jest YYYY-MM-DD -> nic
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
            return {}

        # przykłady napraw:
        # 2026/01/03 -> 2026-01-03
        m = re.fullmatch(r"(\d{4})[\/\.](\d{2})[\/\.](\d{2})", raw)
        if m:
            y, mo, d = m.group(1), m.group(2), m.group(3)
            return {"date": f"{y}-{mo}-{d}"}

        # "03-01-2026" (DD-MM-YYYY) -> YYYY-MM-DD
        m = re.fullmatch(r"(\d{2})-(\d{2})-(\d{4})", raw)
        if m:
            d, mo, y = m.group(1), m.group(2), m.group(3)
            return {"date": f"{y}-{mo}-{d}"}

        return {}

    def _looks_like_transient(self, error: ToolError) -> bool:
        msg = (error.message or "").lower()
        return any(x in msg for x in ["temporar", "timeout", "try again", "rate limit", "too many requests"])
