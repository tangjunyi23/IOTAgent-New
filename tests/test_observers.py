from app.models import AuditEvent, EventKind, NoteEntry
from app.observers import AgentObservationState, ContextWindowObserver, NoteRecallObserver, ToolLoopObserver


async def test_tool_loop_observer_injects_intervention():
    state = AgentObservationState(
        agent_id="a1",
        role="triage",
        system_prompt="prompt",
        notes={},
    )
    observer = ToolLoopObserver(threshold=2)
    event = AuditEvent(kind=EventKind.TOOL_INVOCATION, message="x", payload={"command_key": "file"})
    await observer.handle(event, state)
    generated = await observer.handle(event, state)
    assert generated
    assert state.intervention_history


async def test_note_recall_observer_evicts_note():
    note = NoteEntry(content="core", source="manager", is_core=True)
    state = AgentObservationState(
        agent_id="a1",
        role="triage",
        system_prompt="prompt",
        notes={note.id: note},
    )
    observer = NoteRecallObserver(threshold=2)
    event = AuditEvent(kind=EventKind.NOTE_RETRIEVAL, message="note", payload={"note_id": note.id})
    await observer.handle(event, state)
    generated = await observer.handle(event, state)
    assert generated
    assert state.notes[note.id].invalidated is True


async def test_context_window_observer_resets_messages():
    note = NoteEntry(content="core", source="manager", is_core=True)
    state = AgentObservationState(
        agent_id="a1",
        role="triage",
        system_prompt="prompt",
        notes={note.id: note},
        messages=[{"role": "user", "content": "old"}],
    )
    observer = ContextWindowObserver(threshold=1)
    event = AuditEvent(kind=EventKind.REASONING_ROUND, message="round")
    generated = await observer.handle(event, state)
    assert not generated
    generated = await observer.handle(event, state)
    assert generated
    assert "核心笔记" in state.messages[-1]["content"]
