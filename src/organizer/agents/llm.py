from __future__ import annotations

import os
from organizer.core.agent import Agent
from organizer.core.types import Message


class OpenAIAgent(Agent):
    """
    Agent oparty o OpenAI API.
    Opcjonalny: jeśli brak OPENAI_API_KEY → rzuca czytelny błąd.
    """

    def __init__(self, model: str = "gpt-4o-mini", name: str = "llm"):
        super().__init__(name=name)
        self._model = model

    def handle(self, message: Message) -> Message:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set")

        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        completion = client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": "You are a helpful travel and planning assistant."},
                {"role": "user", "content": message.content},
            ],
        )

        text = completion.choices[0].message.content
        return Message(sender=self.name, content=text)
