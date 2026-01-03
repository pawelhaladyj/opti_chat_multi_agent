from dataclasses import dataclass


@dataclass(frozen=True)
class Preferences:
    """
    Minimalne preferencje użytkownika dla planowania.
    Z czasem rozbudujemy (budżet, tempo, typy aktywności itd.).
    """
    category: str = "any"          # np. "music", "food", "museum"
    max_items: int = 4             # planner wybierze do tylu punktów programu
    event_duration_hours: int = 2  # przyjmujemy stałą długość eventu (heurystyka)

