from organizer.tools import FakeWeatherAPI, FakeEventsAPI, FakeHousingAPI
from organizer.agents import WeatherAgent, StayAgent
from organizer.core.types import Message


def test_fake_weather_api_returns_expected_format():
    api = FakeWeatherAPI()
    data = api(location="Warszawa", date="tomorrow")

    assert set(data.keys()) == {"location", "date", "summary", "temp_c", "precip_prob"}
    assert data["location"] == "Warszawa"
    assert isinstance(data["temp_c"], int)
    assert 0 <= data["precip_prob"] <= 100


def test_fake_events_api_returns_expected_format():
    api = FakeEventsAPI()
    data = api(city="Kraków", date="2026-01-10", category="music")

    assert set(data.keys()) == {"city", "date", "category", "events"}
    assert data["city"] == "Kraków"
    assert data["category"] == "music"
    assert isinstance(data["events"], list)
    assert len(data["events"]) >= 3
    assert {"title", "city", "date", "start", "price_pln", "indoor"} <= set(data["events"][0].keys())


def test_fake_housing_api_returns_expected_format():
    api = FakeHousingAPI()
    data = api(city="Gdańsk", checkin="2026-02-01", checkout="2026-02-03", budget_pln_per_night=250)

    assert set(data.keys()) == {"city", "checkin", "checkout", "budget_pln_per_night", "stays"}
    assert data["city"] == "Gdańsk"
    assert isinstance(data["stays"], list)
    assert len(data["stays"]) >= 3
    assert {"name", "city", "price_pln_per_night", "rating"} <= set(data["stays"][0].keys())


def test_weather_agent_uses_tool_output():
    api = FakeWeatherAPI()
    agent = WeatherAgent(tool=api, name="weather")

    reply = agent.handle(Message(sender="user", content="Jaka będzie pogoda w Warszawie?"))
    assert reply.sender == "weather"
    assert "Warszaw" in reply.content  # Warszawa/Warszawie zależnie od formy
    assert "°C" in reply.content


def test_stay_agent_uses_tool_output():
    api = FakeHousingAPI()
    agent = StayAgent(tool=api, name="stays")

    reply = agent.handle(Message(sender="user", content="Znajdź nocleg w Krakowie"))
    assert reply.sender == "stays"
    assert "Krak" in reply.content
    assert "PLN" in reply.content
