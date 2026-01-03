from organizer.core.agent import Agent
from organizer.core.types import Message


class WeatherAgent(Agent):
    """
    Stub: na razie nie łączy się z żadnym API.
    """

    def __init__(self, name: str = "weather"):
        super().__init__(name=name)

    def handle(self, message: Message) -> Message:
        return Message(
            sender=self.name,
            content="(stub) Mogę sprawdzić pogodę – na razie bez API."
        )
