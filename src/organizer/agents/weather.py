import re
from typing import Optional

from organizer.core.agent import Agent
from organizer.core.types import Message
from organizer.core.tool import Tool


def _extract_location(text: str) -> Optional[str]:
    """
    Bardzo proste wyciąganie lokalizacji: szukamy 'w <Miasto>'.
    Np. 'pogoda w Warszawie' -> 'Warszawie'
    """
    m = re.search(r"\bw\s+([A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż\-]+)", text, re.IGNORECASE)
    return m.group(1) if m else None


class WeatherAgent(Agent):
    def __init__(self, tool: Tool, name: str = "weather", city_normalizer: Tool | None = None):
        super().__init__(name=name)
        self._tool = tool
        self._city_normalizer = city_normalizer

    def handle(self, message: Message) -> Message:
        raw_location = _extract_location(message.content) or "Warszawa"

        # Jeśli mamy normalizator (np. OpenAI) → zamień na mianownik
        if self._city_normalizer is not None:
            norm = self._city_normalizer(text=raw_location)
            location = norm.get("nominative", raw_location)
        else:
            location = raw_location

        date = "tomorrow"
        data = self._tool(location=location, date=date)

        content = (
            f"Pogoda dla {data['location']} ({data['date']}): "
            f"{data['summary']}, {data['temp_c']}°C, "
            f"opady: {data['precip_prob']}%."
        )

        return Message(sender=self.name, content=content)
