from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from organizer.core.trace import TraceEvent


def write_trace_jsonl(events: Iterable[TraceEvent], path: str | Path) -> Path:
    """
    Zapisuje trace (team_conversation) do pliku JSONL.
    Jeden event = jedna linia JSON.

    Uwaga: To jest celowo proste. Docelowo można dodać rotację, kompresję, itp.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    with p.open("w", encoding="utf-8") as f:
        for ev in events:
            f.write(json.dumps(ev.__dict__, ensure_ascii=False) + "\n")

    return p
