import re
from typing import Optional

from organizer.core.agent import Agent
from organizer.core.types import Message
from organizer.core.tool import Tool


def _extract_city(text: str) -> Optional[str]:
    m = re.search(r"\bw\s+([A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż\-]+)", text, re.IGNORECASE)
    return m.group(1) if m else None


class StayAgent(Agent):
    def __init__(self, tool: Tool, name: str = "stays"):
        super().__init__(name=name)
        self._tool = tool

    def handle(self, message: Message) -> Message:
        city = _extract_city(message.content) or "Kraków"
        checkin, checkout = "2026-01-10", "2026-01-12"

        data = self._tool(city=city, checkin=checkin, checkout=checkout, budget_pln_per_night=300)
        stays = data["stays"]

        top = stays[0]
        content = (
            f"Znalazłem {len(stays)} propozycje noclegu w {data['city']} "
            f"({data['checkin']}–{data['checkout']}). "
            f"Najtańsza przykładowa: {top['name']} za {top['price_pln_per_night']} PLN/noc "
            f"(ocena {top['rating']})."
        )

        return Message(sender=self.name, content=content)
