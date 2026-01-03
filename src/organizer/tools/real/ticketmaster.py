from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date as Date, datetime, timedelta, timezone
from typing import Any

import httpx


@dataclass(frozen=True)
class TicketmasterEventsTool:
    """
    Realne wydarzenia z Ticketmaster Discovery API.

    Wymaga zmiennej środowiskowej:
    - TICKETMASTER_API_KEY
    """
    name: str = "ticketmaster_events"
    base_url: str = "https://app.ticketmaster.com/discovery/v2/events.json"

    def __call__(self, *, city: str, date: str, category: str = "any") -> dict[str, Any]:
        api_key = os.getenv("TICKETMASTER_API_KEY")
        if not api_key:
            raise RuntimeError("Missing env var: TICKETMASTER_API_KEY")

        day = self._resolve_date(date)
        start = datetime(day.year, day.month, day.day, 0, 0, tzinfo=timezone.utc)
        end = start + timedelta(days=1)

        params = {
            "apikey": api_key,
            "city": city,
            "size": 20,
            "startDateTime": start.isoformat().replace("+00:00", "Z"),
            "endDateTime": end.isoformat().replace("+00:00", "Z"),
        }

        # proste mapowanie kategorii -> classificationName (Ticketmaster przykłady)
        if category != "any":
            params["classificationName"] = category

        with httpx.Client(timeout=10.0) as client:
            r = client.get(self.base_url, params=params)
            r.raise_for_status()
            raw = r.json()

        events_out = []
        embedded = (raw.get("_embedded") or {}).get("events") or []
        for ev in embedded:
            name = ev.get("name", "Untitled")
            dates = ev.get("dates", {}).get("start", {})
            local_dt = dates.get("localDate", day.isoformat())
            local_time = dates.get("localTime", "19:00:00")

            # format zgodny z naszym wcześniejszym kontraktem eventów
            start_hhmm = local_time[:5] if isinstance(local_time, str) else "19:00"

            # indoor/outdoor: Ticketmaster nie zawsze daje to wprost — heurystyka: venue name exists => indoor True
            venues = (((ev.get("_embedded") or {}).get("venues")) or [])
            indoor_guess = True if venues else True

            events_out.append(
                {
                    "title": name,
                    "city": city,
                    "date": local_dt,
                    "start": start_hhmm,
                    "price_pln": None,   # API może nie dać ceny bez dodatkowych pól/źródeł
                    "indoor": indoor_guess,
                }
            )

        return {"city": city, "date": day.isoformat(), "category": category, "events": events_out, "source": "ticketmaster"}

    def _resolve_date(self, date_str: str) -> Date:
        if date_str.lower() == "tomorrow":
            return (datetime.now(timezone.utc) + timedelta(days=1)).date()
        return Date.fromisoformat(date_str)
