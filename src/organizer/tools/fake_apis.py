from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any


def _seed_int(*parts: str) -> int:
    """
    Stabilny 'seed' liczbowy z tekstu (deterministyczny między uruchomieniami).
    """
    joined = "|".join(parts).encode("utf-8")
    digest = hashlib.md5(joined).hexdigest()
    return int(digest[:8], 16)


@dataclass(frozen=True)
class FakeWeatherAPI:
    name: str = "fake_weather_api"

    def __call__(self, *, location: str, date: str) -> dict[str, Any]:
        s = _seed_int(location.lower(), date)
        temp_c = (s % 35) - 5              # -5..29
        precip_prob = (s // 7) % 101       # 0..100
        summary = "deszczowo" if precip_prob > 60 else "pogodnie"

        return {
            "location": location,
            "date": date,
            "summary": summary,
            "temp_c": temp_c,
            "precip_prob": precip_prob,
        }


@dataclass(frozen=True)
class FakeEventsAPI:
    name: str = "fake_events_api"

    def __call__(self, *, city: str, date: str, category: str = "any") -> dict[str, Any]:
        s = _seed_int(city.lower(), date, category.lower())
        n = 3 + (s % 3)  # 3..5 wydarzeń

        events = []
        for i in range(n):
            start_hour = 16 + ((s + i * 3) % 6)  # 16..21
            events.append(
                {
                    "title": f"{category.title()} Event {i+1}",
                    "city": city,
                    "date": date,
                    "start": f"{start_hour:02d}:00",
                    "price_pln": 20 + ((s + i * 11) % 120),
                    "indoor": ((s + i) % 2 == 0),
                }
            )

        return {"city": city, "date": date, "category": category, "events": events}


@dataclass(frozen=True)
class FakeHousingAPI:
    name: str = "fake_housing_api"

    def __call__(
        self,
        *,
        city: str,
        checkin: str,
        checkout: str,
        budget_pln_per_night: int = 300,
    ) -> dict[str, Any]:
        s = _seed_int(city.lower(), checkin, checkout, str(budget_pln_per_night))
        n = 3 + (s % 3)  # 3..5 ofert

        stays = []
        for i in range(n):
            price = max(80, budget_pln_per_night - ((s + i * 37) % 150))
            stays.append(
                {
                    "name": f"Stay {i+1} in {city}",
                    "city": city,
                    "price_pln_per_night": price,
                    "rating": round(3.5 + (((s + i * 5) % 15) / 10), 1),  # 3.5..5.0
                }
            )

        return {
            "city": city,
            "checkin": checkin,
            "checkout": checkout,
            "budget_pln_per_night": budget_pln_per_night,
            "stays": stays,
        }

