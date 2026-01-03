import os
import pytest

from organizer.tools.real import TicketmasterEventsTool


@pytest.mark.integration
def test_ticketmaster_events_tool_works_if_api_key_present():
    if not os.getenv("TICKETMASTER_API_KEY"):
        pytest.skip("TICKETMASTER_API_KEY not set")

    tool = TicketmasterEventsTool()
    data = tool(city="Warsaw", date="tomorrow", category="music")

    assert data["source"] == "ticketmaster"
    assert data["city"] == "Warsaw"
    assert isinstance(data["events"], list)
