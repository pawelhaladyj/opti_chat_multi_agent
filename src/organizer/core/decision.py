from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional, List, Type


@dataclass(frozen=True)
class CoordinatorDecision:
    """
    Twarda decyzja koordynatora (JSON-kontrakt).
    """
    next_agent: str
    task: str
    expected_output: str
    stop: bool = False
    needed_tools: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "next_agent": self.next_agent,
            "task": self.task,
            "expected_output": self.expected_output,
            "stop": self.stop,
            "needed_tools": list(self.needed_tools),
        }

    @classmethod
    def from_dict(cls: Type["CoordinatorDecision"], data: Mapping[str, Any]) -> "CoordinatorDecision":
        return cls(
            next_agent=str(data.get("next_agent", "")),
            task=str(data.get("task", "")),
            expected_output=str(data.get("expected_output", "")),
            stop=bool(data.get("stop", False)),
            needed_tools=list(data.get("needed_tools", []) or []),
        )

    def validate(self) -> None:
        if not self.next_agent.strip():
            raise ValueError("CoordinatorDecision.next_agent must be non-empty")
        if not self.task.strip():
            raise ValueError("CoordinatorDecision.task must be non-empty")
        if not self.expected_output.strip():
            raise ValueError("CoordinatorDecision.expected_output must be non-empty")
