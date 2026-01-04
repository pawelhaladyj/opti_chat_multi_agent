from __future__ import annotations

from typing import Iterable, List, Optional

from organizer.core.types import Event, Message


def replay_history_from_events(events: Iterable[Event]) -> List[Message]:
    """
    Minimalny replay: odtwarza historię odpowiedzi agentów na podstawie eventów typu 'respond'.

    Cel testowy: udowodnić, że Event jest wystarczająco ustrukturyzowany,
    aby można było odtwarzać przebieg bez dostępu do runtime.
    """
    out: List[Message] = []
    for ev in events:
        if ev.type != "respond":
            continue
        content = str(ev.data.get("content", ""))
        sender = ev.actor or "agent"
        out.append(
            Message(
                sender=sender,
                content=content,
                correlation_id=ev.correlation_id,
                meta={"replayed": True},
            )
        )
    return out
