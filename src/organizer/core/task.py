from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class Task:
    """
    Minimalny opis zadania, który pomoże RecoveryAgent zrozumieć intencję
    bez analizowania wypowiedzi usera.
    """
    name: str                 # np. "weather_lookup", "events_search"
    target: str               # np. "open_meteo_geocoding"
    inputs: Mapping[str, Any] # parametry, które poszły do tool-a
