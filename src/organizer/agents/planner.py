from __future__ import annotations

import re
from typing import Any, Optional

from organizer.core.agent import Agent
from organizer.core.tool import Tool
from organizer.core.types import Message
from organizer.core.preferences import Preferences


def _extract_city(text: str) -> Optional[str]:
    # bardzo prosto: "w Krakowie", "w Warszawie"
    m = re.search(r"\bw\s+([A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż\-]+)", text, re.IGNORECASE)
    return m.group(1) if m else None


def _parse_hour(hhmm: str) -> int:
    # "18:00" -> 18
    return int(hhmm.split(":")[0])


class PlannerAgent(Agent):
    """
    Agent planista:
    - pobiera pogodę i listę eventów przez narzędzia (toole),
    - wybiera 2–4 punkty (heurystyka),
    - układa prostą oś czasu,
    - unika nakładania się eventów.
    """

    def __init__(
        self,
        *,
        weather_tool: Tool,
        events_tool: Tool,
        preferences: Preferences | None = None,
        name: str = "planner",
    ):
        super().__init__(name=name)
        self._weather_tool = weather_tool
        self._events_tool = events_tool
        self._prefs = preferences or Preferences()

    def handle(self, message: Message) -> Message:
        city = _extract_city(message.content) or "Warszawa"
        date = "tomorrow"  # na razie stałe; później dodamy parser dat/czasu

        weather: dict[str, Any] = self._weather_tool(location=city, date=date)
        events_payload: dict[str, Any] = self._events_tool(city=city, date=date, category=self._prefs.category)
        events: list[dict[str, Any]] = list(events_payload.get("events", []))

        rainy = int(weather.get("precip_prob", 0)) > 60

        # 1) Filtr: przy deszczu bierzemy tylko indoor
        if rainy:
            events = [e for e in events if e.get("indoor") is True]

        # 2) Sortujemy po godzinie startu
        events.sort(key=lambda e: _parse_hour(e["start"]))

        # 3) Wybór bez nakładania (greedy)
        chosen: list[dict[str, Any]] = []
        last_end_hour: Optional[int] = None

        for e in events:
            start = _parse_hour(e["start"])
            end = start + self._prefs.event_duration_hours

            if last_end_hour is None or start >= last_end_hour:
                chosen.append(e)
                last_end_hour = end

            if len(chosen) >= self._prefs.max_items:
                break

        # Heurystyka “2–4”: jeśli mamy >=2, super; jeśli mniej, zwracamy ile jest.
        if not chosen:
            content = (
                f"Nie znalazłem sensownego planu dla {city} ({date}). "
                f"Pogoda: {weather.get('summary','?')}."
            )
            return Message(sender=self.name, content=content)

        # Budujemy odpowiedź “dla człowieka”
        lines = []
        lines.append(f"Plan dla {city} ({date})")
        lines.append(f"Pogoda: {weather.get('summary','?')}, {weather.get('temp_c','?')}°C, opady {weather.get('precip_prob','?')}%")
        lines.append("Oś czasu:")

        for e in chosen:
            lines.append(f"- {e['start']} — {e['title']} ({'indoor' if e.get('indoor') else 'outdoor'}, {e.get('price_pln','?')} PLN)")

        if rainy:
            lines.append("Uwzględniłem tylko wydarzenia indoor, bo wygląda na deszcz.")

        return Message(sender=self.name, content="\n".join(lines))

