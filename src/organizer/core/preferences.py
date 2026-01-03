from dataclasses import dataclass


@dataclass(frozen=True)
class Preferences:
    """
    Minimalne preferencje użytkownika.

    Uwaga: frozen=True -> obiekt niemutowalny, więc aktualizacje robimy przez
    tworzenie nowej instancji (to jest bezpieczne i testowalne).
    """
    favorite_city: str = "Warszawa"
    budget_pln_per_night: int = 300
    category: str = "any"          # np. "music", "food", "museum"

    max_items: int = 4
    event_duration_hours: int = 2

