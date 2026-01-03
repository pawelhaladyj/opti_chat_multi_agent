from __future__ import annotations

from dataclasses import dataclass
from datetime import date as Date, datetime, timedelta, timezone
from typing import Any

import httpx


@dataclass(frozen=True)
class OpenMeteoGeocodingTool:
    """
    Zamienia nazwę miejsca na współrzędne (lat/lon) przez Open-Meteo Geocoding API.
    """
    name: str = "open_meteo_geocoding"
    base_url: str = "https://geocoding-api.open-meteo.com/v1/search"

    def __call__(self, *, location: str, count: int = 1, language: str = "en") -> dict[str, Any]:
        params = {"name": location, "count": count, "language": language, "format": "json"}
        with httpx.Client(timeout=10.0) as client:
            r = client.get(self.base_url, params=params)
            r.raise_for_status()
            return r.json()


@dataclass(frozen=True)
class OpenMeteoWeatherTool:
    """
    Realne narzędzie pogodowe:
    - geokoduje nazwę miasta do lat/lon,
    - pobiera prognozę godzinową,
    - zwraca uproszczony format: summary/temp/precip_prob dla wybranego dnia (domyślnie 'tomorrow').
    """
    name: str = "open_meteo_weather"
    forecast_url: str = "https://api.open-meteo.com/v1/forecast"
    geocoding: OpenMeteoGeocodingTool = OpenMeteoGeocodingTool()

    def __call__(self, *, location: str, date: str) -> dict[str, Any]:
        lat, lon, resolved_name = self._geocode(location)

        target = self._resolve_date(date)

        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "temperature_2m,precipitation_probability",
            "timezone": "auto",
            "timeformat": "iso8601",
            "forecast_days": 7,
        }

        with httpx.Client(timeout=10.0) as client:
            r = client.get(self.forecast_url, params=params)
            r.raise_for_status()
            data = r.json()

        # wybieramy godzinę około południa (12:00) w danym dniu, jeśli istnieje
        hourly = data.get("hourly", {})
        times: list[str] = hourly.get("time", [])
        temps: list[float] = hourly.get("temperature_2m", [])
        precs: list[float] = hourly.get("precipitation_probability", [])

        chosen_temp, chosen_prec = self._pick_midday(times, temps, precs, target)

        summary = "deszczowo" if chosen_prec > 60 else "pogodnie"

        return {
            "location": resolved_name,
            "date": target.isoformat(),
            "summary": summary,
            "temp_c": int(round(chosen_temp)),
            "precip_prob": int(round(chosen_prec)),
            "source": "open-meteo",
        }

    def _geocode(self, location: str) -> tuple[float, float, str]:
        geo = self.geocoding(location=location, count=1, language="en")
        results = geo.get("results") or []
        if not results:
            raise RuntimeError(f"Open-Meteo geocoding: no results for '{location}'")

        top = results[0]
        lat = float(top["latitude"])
        lon = float(top["longitude"])
        name = str(top.get("name", location))
        country = str(top.get("country", "")).strip()
        resolved = f"{name}, {country}".strip(", ")
        return lat, lon, resolved

    def _resolve_date(self, date_str: str) -> Date:
        if date_str.lower() == "tomorrow":
            # UTC->Date jest OK jako przybliżenie; Open-Meteo i tak zwróci lokalne czasy przy timezone=auto
            return (datetime.now(timezone.utc) + timedelta(days=1)).date()

        # oczekujemy YYYY-MM-DD
        return Date.fromisoformat(date_str)

    def _pick_midday(
        self,
        times: list[str],
        temps: list[float],
        precs: list[float],
        target: Date,
    ) -> tuple[float, float]:
        # szukamy wpisu "YYYY-MM-DDT12:00"
        target_prefix = target.isoformat() + "T12:00"
        for i, t in enumerate(times):
            if t.startswith(target_prefix):
                return float(temps[i]), float(precs[i])

        # fallback: pierwszy wpis z danego dnia
        day_prefix = target.isoformat() + "T"
        for i, t in enumerate(times):
            if t.startswith(day_prefix):
                return float(temps[i]), float(precs[i])

        raise RuntimeError("Open-Meteo forecast: no hourly data for target day")
