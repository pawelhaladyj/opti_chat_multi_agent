from organizer.core.memory import TeamMemory
from organizer.core.types import Event


def test_team_memory_rolling_summary_triggers_every_n_events():
    mem = TeamMemory(summarize_every=4, keep_recent=10, keep_scratchpad=5)

    for i in range(4):
        mem.add_event(Event(type="decision", actor="coordinator", target="agent", data={"i": i}))

    ctx = mem.context()
    assert ctx.rolling_summary != ""
    assert mem.summary.condensed_events == 4
    # scratchpad powinien być krótki
    assert len(ctx.scratchpad) <= 5


def test_team_memory_facts_are_separate_from_scratchpad():
    mem = TeamMemory(summarize_every=3, keep_recent=10, keep_scratchpad=5)
    mem.add_facts("User prefers hotels", "City=Warszawa")
    mem.add_event(Event(type="tool_call", actor="tool_runner", target="open_meteo", data={"q": "Warszawa"}))

    ctx = mem.context()
    assert "User prefers hotels" in ctx.facts
    assert "City=Warszawa" in ctx.facts
    # facts nie mieszają się do scratchpad automatycznie
    assert all("User prefers hotels" not in s for s in ctx.scratchpad)

