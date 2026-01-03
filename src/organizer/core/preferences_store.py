from __future__ import annotations

from dataclasses import replace
from typing import Dict

from organizer.core.preferences import Preferences


class PreferencesStore:
    """
    Najprostsza pamięć preferencji: słownik w RAM.

    Klucz: user_id (np. "pawel", "user-123")
    Wartość: Preferences
    """

    def __init__(self, default: Preferences | None = None):
        self._default = default or Preferences()
        self._by_user: Dict[str, Preferences] = {}

    def get(self, user_id: str) -> Preferences:
        """
        Zwraca preferencje użytkownika. Jeśli brak, zwraca defaulty.
        """
        return self._by_user.get(user_id, self._default)

    def set(self, user_id: str, preferences: Preferences) -> None:
        """
        Ustawia pełny zestaw preferencji.
        """
        self._by_user[user_id] = preferences

    def update(self, user_id: str, **changes) -> Preferences:
        """
        Aktualizuje tylko wybrane pola (np. budget, category).
        Zwraca nowy obiekt Preferences.
        """
        current = self.get(user_id)
        updated = replace(current, **changes)
        self._by_user[user_id] = updated
        return updated
