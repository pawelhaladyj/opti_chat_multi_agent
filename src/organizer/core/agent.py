from abc import ABC, abstractmethod
from organizer.core.types import Message


class Agent(ABC):
    """
    Abstrakcyjna rola poznawcza w systemie.
    """

    def __init__(self, name: str):
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @abstractmethod
    def handle(self, message: Message) -> Message:
        """
        Agent przyjmuje wiadomość i zwraca odpowiedź.
        """
        raise NotImplementedError
