from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentCapability:
    """
    Opis kompetencji agenta przekazywany do koordynatora.
    Umieszczone w core, aby core nie importował organizer.agents.* (unikamy cykli).
    """
    name: str
    description: str
