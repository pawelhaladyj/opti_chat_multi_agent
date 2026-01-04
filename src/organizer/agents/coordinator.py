from __future__ import annotations

from typing import List

from organizer.core.agent import Agent
from organizer.core.types import Message
from organizer.core.decision import CoordinatorDecision
from organizer.core.memory import TeamMemoryContext
from organizer.core.capabilities import AgentCapability  # <-- nowy import


class CoordinatorAgent(Agent):
    """
    CoordinatorAgent = jedyny decydent routingu.

    W iteracji 16 deterministyczny coordinator (heurystyka),
    ale kontrakt identyczny jak dla LLM: zwraca CoordinatorDecision (JSON).
    """

    def __init__(self, *, name: str = "coordinator"):
        super().__init__(name=name)

    def handle(self, message: Message) -> Message:
        return Message(sender=self.name, content="CoordinatorAgent does not respond directly.")

    def decide(
        self,
        *,
        user_goal: str,
        team_ctx: TeamMemoryContext,
        agents: List[AgentCapability],
    ) -> CoordinatorDecision:
        text = (user_goal or "").strip()
        low = text.lower()

        if low in {"exit", "quit"} or low.startswith("koniec"):
            return CoordinatorDecision(
                next_agent="coordinator",
                task="Stop conversation",
                expected_output="No further action",
                stop=True,
            )

        weather_intent = any(k in low for k in ["pogoda", "prognoza", "temperatura", "pada", "wiatr", "wiało", "pochmurnie"])
        stays_intent = any(k in low for k in ["nocleg", "hotel", "apartament", "mieszkanie", "zostań", "stay"])
        plan_intent = any(k in low for k in ["zaplanuj", "plan", "itinerarz", "zorganizuj", "dzień", "czas"])

        available = {a.name: a for a in agents}

        if weather_intent and "weather" in available:
            return CoordinatorDecision(
                next_agent="weather",
                task=f"Odpowiedz na pytanie pogodowe: {text}",
                expected_output="Krótka prognoza i uzasadnienie (miasto/dzień/warunki).",
                needed_tools=["weather_tool"],
            )

        if stays_intent and "stays" in available:
            return CoordinatorDecision(
                next_agent="stays",
                task=f"Pomóż znaleźć nocleg / opcje zakwaterowania: {text}",
                expected_output="Lista opcji + krótkie uzasadnienie wyboru.",
                needed_tools=["housing_tool"],
            )

        if plan_intent and "planner" in available:
            return CoordinatorDecision(
                next_agent="planner",
                task=f"Zaplanuj aktywności: {text}",
                expected_output="Proponowany plan dnia + punkty + warunki pogodowe jeśli istotne.",
                needed_tools=["events_tool", "weather_tool"],
            )

        if "planner" in available:
            return CoordinatorDecision(
                next_agent="planner",
                task=f"Spróbuj zinterpretować intencję i pomóc: {text}",
                expected_output="Zwięzła odpowiedź + ewentualne pytanie doprecyzowujące.",
            )

        first = agents[0].name if agents else "coordinator"
        return CoordinatorDecision(
            next_agent=first,
            task=f"Odpowiedz najlepiej jak potrafisz: {text}",
            expected_output="Odpowiedź zgodna z kompetencjami.",
        )
