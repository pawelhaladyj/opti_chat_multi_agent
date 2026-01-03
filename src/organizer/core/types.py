from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Message:
    """
    Reprezentuje pojedynczą wypowiedź w systemie.
    """
    sender: str          # np. "user", "weather_agent"
    content: str


@dataclass(frozen=True)
class ToolResult:
    """
    Wynik działania narzędzia (API).
    """
    tool_name: str
    payload: Any
