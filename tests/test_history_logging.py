from organizer.core.history_logger import HistoryLogger
from organizer.core.types import Message


def test_history_logger_appends_lines(tmp_path):
    logger = HistoryLogger(history_dir=tmp_path, session_timestamp="20260103_120000")

    logger.append(Message(sender="user", content="hej"))
    logger.append(Message(sender="weather", content="pogodnie"))

    content = logger.file_path.read_text(encoding="utf-8")
    assert "[user] hej" in content
    assert "[weather] pogodnie" in content
