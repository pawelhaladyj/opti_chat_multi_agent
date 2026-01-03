from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from organizer.core.types import Message


@dataclass
class HistoryLogger:
    """
    Prosty logger rozmów:
    - tworzy folder history/ jeśli nie istnieje
    - tworzy plik history_<timestamp>.txt
    - dopisuje kolejne linie (append)
    """
    history_dir: Path
    session_timestamp: str

    @classmethod
    def create_default(cls) -> "HistoryLogger":
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        history_dir = Path("history")
        history_dir.mkdir(parents=True, exist_ok=True)
        return cls(history_dir=history_dir, session_timestamp=ts)

    @property
    def file_path(self) -> Path:
        return self.history_dir / f"history_{self.session_timestamp}.txt"

    def append(self, msg: Message) -> None:
        line_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{line_ts}] [{msg.sender}] {msg.content}\n"
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        with self.file_path.open("a", encoding="utf-8") as f:
            f.write(line)
