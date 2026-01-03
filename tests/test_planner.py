from organizer.agents import PlannerAgent
from organizer.core.types import Message
from organizer.core.preferences import Preferences


class FixedWeatherTool:
    name = "fixed_weather"

    def __init__(self, *, precip_prob: int, summary: str = "pogodnie", temp_c: int = 20):
        self._precip_prob = precip_prob
        self._summary = summary
        self._temp_c = temp_c

    def __call__(self, *, location: str, date: str):
        return {
            "location": location,
            "date": date,
            "summary": self._summary,
            "temp_c": self._temp_c,
            "precip_prob": self._precip_prob,
        }


class FixedEventsTool:
    name = "fixed_events"

    def __init__(self, events):
        self._events = events

    def __call__(self, *, city: str, date: str, category: str = "any"):
        return {"city": city, "date": date, "category": category, "events": list(self._events)}


def test_rainy_weather_selects_only_indoor_events():
    weather = FixedWeatherTool(precip_prob=90, summary="deszczowo")
    events = FixedEventsTool(
        [
            {"title": "Outdoor Walk", "city": "X", "date": "tomorrow", "start": "16:00", "price_pln": 0, "indoor": False},
            {"title": "Museum", "city": "X", "date": "tomorrow", "start": "17:00", "price_pln": 30, "indoor": True},
            {"title": "Indoor Concert", "city": "X", "date": "tomorrow", "start": "19:00", "price_pln": 80, "indoor": True},
        ]
    )

    planner = PlannerAgent(weather_tool=weather, events_tool=events, preferences=Preferences(max_items=4))
    reply = planner.handle(Message(sender="user", content="Ułóż mi plan w Krakowie"))

    assert reply.sender == "planner"
    assert "Outdoor Walk" not in reply.content
    assert "Museum" in reply.content
    assert "Indoor Concert" in reply.content
    assert "tylko wydarzenia indoor" in reply.content.lower()


def test_good_weather_allows_outdoor_events():
    weather = FixedWeatherTool(precip_prob=10, summary="pogodnie")
    events = FixedEventsTool(
        [
            {"title": "Outdoor Market", "city": "X", "date": "tomorrow", "start": "16:00", "price_pln": 0, "indoor": False},
            {"title": "Indoor Cinema", "city": "X", "date": "tomorrow", "start": "18:00", "price_pln": 35, "indoor": True},
        ]
    )

    planner = PlannerAgent(weather_tool=weather, events_tool=events, preferences=Preferences(max_items=4))
    reply = planner.handle(Message(sender="user", content="Plan dnia w Gdańsku proszę"))

    assert "Outdoor Market" in reply.content
    assert "Indoor Cinema" in reply.content


def test_planner_does_not_pick_overlapping_events():
    # deszcz nieistotny dla overlap testu — dajemy pogodnie
    weather = FixedWeatherTool(precip_prob=0, summary="pogodnie")
    events = FixedEventsTool(
        [
            # start 16:00 (trwa 2h -> do 18:00)
            {"title": "Event A", "city": "X", "date": "tomorrow", "start": "16:00", "price_pln": 10, "indoor": True},
            # start 17:00 (nakłada się z A) -> powinien zostać odrzucony
            {"title": "Event B", "city": "X", "date": "tomorrow", "start": "17:00", "price_pln": 10, "indoor": True},
            # start 18:00 (nie nakłada się) -> powinien wejść
            {"title": "Event C", "city": "X", "date": "tomorrow", "start": "18:00", "price_pln": 10, "indoor": True},
        ]
    )

    planner = PlannerAgent(
        weather_tool=weather,
        events_tool=events,
        preferences=Preferences(max_items=4, event_duration_hours=2),
    )
    reply = planner.handle(Message(sender="user", content="Ułóż plan w Warszawie"))

    assert "Event A" in reply.content
    assert "Event C" in reply.content
    assert "Event B" not in reply.content
