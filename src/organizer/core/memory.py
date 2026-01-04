from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any, Iterable, Optional

from organizer.core.types import Event


@dataclass
class RollingSummary:
    """
    Prosty 'rolling summary' bez LLM:
    przechowuje kolejne bloki streszczeń oraz liczniki kondensacji.
    """
    blocks: List[str] = field(default_factory=list)
    condensed_events: int = 0

    def add_block(self, text: str, *, count: int) -> None:
        self.blocks.append(text)
        self.condensed_events += count

    @property
    def text(self) -> str:
        return "\n".join(self.blocks).strip()


@dataclass
class TeamMemoryContext:
    """
    To jest to, co koordynator/agenci dostają jako kontekst:
    - rolling_summary: streszczenie starszych zdarzeń
    - facts: ustalenia trwałe
    - scratchpad: robocze kroki (krótkie, ostatnie)
    - recent_events: ostatnie eventy w surowej formie (ograniczone)
    """
    rolling_summary: str
    facts: List[str]
    scratchpad: List[str]
    recent_events: List[Event]


@dataclass
class TeamMemory:
    """
    Pamięć zespołu MAS:
    - events: pełny strumień eventów (może rosnąć, ale kondensujemy kontekst)
    - rolling_summary co N eventów
    - facts osobno od scratchpad

    Konfiguracja:
    - summarize_every: co ile eventów robimy nowy blok summary
    - keep_recent: ile ostatnich eventów trzymamy jako 'recent_events'
    - keep_scratchpad: ile wpisów scratchpad trzymamy (najświeższe)
    """
    summarize_every: int = 12
    keep_recent: int = 20
    keep_scratchpad: int = 12

    events: List[Event] = field(default_factory=list)
    summary: RollingSummary = field(default_factory=RollingSummary)
    facts: List[str] = field(default_factory=list)
    scratchpad: List[str] = field(default_factory=list)

    _last_summarized_index: int = 0

    def add_event(self, ev: Event) -> None:
        self.events.append(ev)
        self._append_to_scratchpad(ev)
        self._maybe_condense()

    def add_facts(self, *facts: str) -> None:
        for f in facts:
            f = (f or "").strip()
            if not f:
                continue
            if f not in self.facts:
                self.facts.append(f)

    def clear(self) -> None:
        self.events.clear()
        self.summary = RollingSummary()
        self.facts.clear()
        self.scratchpad.clear()
        self._last_summarized_index = 0

    def context(self) -> TeamMemoryContext:
        recent = self.events[-self.keep_recent :] if self.keep_recent > 0 else []
        return TeamMemoryContext(
            rolling_summary=self.summary.text,
            facts=list(self.facts),
            scratchpad=list(self.scratchpad[-self.keep_scratchpad :]),
            recent_events=list(recent),
        )

    # ---------- internal ----------

    def _append_to_scratchpad(self, ev: Event) -> None:
        # scratchpad to krótkie „co się stało” (robocze kroki)
        # cel: nie wrzucać całych payloadów, tylko minimalny opis
        payload_hint = ""
        if ev.type in {"tool_call", "observation", "critique", "decision", "error"}:
            # wyciągamy 1-2 klucze dla zwięzłości
            keys = list(ev.data.keys())[:2]
            slim = {k: ev.data.get(k) for k in keys}
            payload_hint = f" data={slim}" if slim else ""

        line = f"{ev.type} :: {ev.actor} -> {ev.target}{payload_hint}"
        self.scratchpad.append(line)

        # ograniczamy rozrost scratchpada
        if len(self.scratchpad) > max(self.keep_scratchpad * 3, 30):
            self.scratchpad = self.scratchpad[-max(self.keep_scratchpad * 2, 20) :]

    def _maybe_condense(self) -> None:
        # rolling summary co N eventów (od ostatniej kondensacji)
        n = self.summarize_every
        if n <= 0:
            return

        pending = len(self.events) - self._last_summarized_index
        if pending < n:
            return

        chunk = self.events[self._last_summarized_index : self._last_summarized_index + n]
        block = self._summarize_chunk(chunk)

        self.summary.add_block(block, count=len(chunk))
        self._last_summarized_index += len(chunk)

        # po kondensacji scratchpad zostawiamy „świeże” wpisy
        self.scratchpad = self.scratchpad[-self.keep_scratchpad :]

    def _summarize_chunk(self, chunk: Iterable[Event]) -> str:
        # deterministyczne streszczenie: licznik typów + kilka najważniejszych
        counts: Dict[str, int] = {}
        highlights: List[str] = []

        for ev in chunk:
            counts[ev.type] = counts.get(ev.type, 0) + 1

            if ev.type in {"decision", "critique", "error"}:
                # te typy są „ważniejsze” – wrzucamy highlight
                hint = self._short_data(ev.data)
                highlights.append(f"- {ev.type}: {ev.actor}->{ev.target}{hint}")

            if ev.type == "tool_call":
                hint = self._short_data(ev.data)
                highlights.append(f"- tool_call: {ev.target}{hint}")

        # header: liczniki
        parts = [f"[summary] +{len(list(chunk))} events "]
        parts.append("counts=" + ", ".join(f"{k}:{v}" for k, v in sorted(counts.items())))

        # ograniczamy highlighty
        if highlights:
            parts.append("highlights:\n" + "\n".join(highlights[:6]))

        return "\n".join(parts)

    @staticmethod
    def _short_data(data: Dict[str, Any]) -> str:
        if not data:
            return ""
        keys = list(data.keys())[:2]
        slim = {k: data.get(k) for k in keys}
        return f" data={slim}"
