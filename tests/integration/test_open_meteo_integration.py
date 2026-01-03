import pytest

from organizer.tools.real import OpenMeteoWeatherTool


@pytest.mark.integration
def test_open_meteo_weather_tool_works():
    tool = OpenMeteoWeatherTool()
    data = tool(location="Warsaw", date="tomorrow")

    assert data["source"] == "open-meteo"
    assert "location" in data
    assert "temp_c" in data
    assert 0 <= data["precip_prob"] <= 100
