from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Literal


FixAction = Literal[
    "retry_same",          # ponów to samo (np. transient)
    "retry_with_params",   # ponów z poprawionymi parametrami
    "fallback_tool",       # użyj innego narzędzia/providera
    "fail"                 # nie da się sensownie naprawić
]


@dataclass(frozen=True)
class FixPlan:
    """
    Plan naprawy po błędzie tool-a.

    action:
      - retry_same: ponów bez zmian
      - retry_with_params: ponów z params_patch
      - fallback_tool: zmień tool na fallback_tool_name (+ params_patch)
      - fail: zakończ

    reason: krótkie uzasadnienie
    params_patch: tylko zmiany (diff), nie całość
    fallback_tool_name: nazwa alternatywnego tool-a (jeśli action="fallback_tool")
    """
    action: FixAction
    reason: str
    params_patch: Mapping[str, Any] | None = None
    fallback_tool_name: str | None = None
