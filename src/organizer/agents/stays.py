from organizer.core.agent import Agent
from organizer.core.types import Message


class StayAgent(Agent):
    """
    Stub: na razie nie łączy się z żadnym API.
    """

    def __init__(self, name: str = "stays"):
        super().__init__(name=name)

    def handle(self, message: Message) -> Message:
        return Message(
            sender=self.name,
            content="(stub) Mogę poszukać noclegu – na razie bez API."
        )
