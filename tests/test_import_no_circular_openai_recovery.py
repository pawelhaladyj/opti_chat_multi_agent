def test_import_openai_recovery_tool_does_not_cause_circular_import():
    # samo importowanie nie powinno wywoływać cykli importów
    from organizer.tools.real.openai_recovery import OpenAIRecoveryTool

    assert OpenAIRecoveryTool is not None
