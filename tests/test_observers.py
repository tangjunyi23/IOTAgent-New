from app.models import AuditEvent, EventKind, NoteEntry
from app.observers import (
    AgentObservationState,
    ContextCompressionObserver,
    ContextWindowObserver,
    NoteRecallObserver,
    ToolLoopObserver,
)


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


class _FakeCompressBackend:
    def __init__(self, summary: str) -> None:
        self.summary = summary
        self.calls = 0

    async def compress_context(self, *, messages, selection):
        self.calls += 1
        return _FakeReply(self.summary)


class _FakeReply:
    def __init__(self, content: str) -> None:
        self.content = content


class _FakeSettings:
    context_length = 40  # tiny so a few messages exceed it
    context_compression_ratio = 0.4
    context_compress_model = "cmp-model"
    manager_regular_model = "reg-model"


async def test_context_compression_observer_compresses_old_messages():
    """When token count exceeds context_length, the observer compresses older
    messages into a summary while keeping the system prompt + recent messages."""
    settings = _FakeSettings()
    backend = _FakeCompressBackend("SUMMARY: gets overflow at 0x80486ae")
    observer = ContextCompressionObserver(settings, backend)

    state = AgentObservationState(
        agent_id="a1",
        role="static-analysis",
        system_prompt="system-prompt",
        notes={},
        messages=[
            {"role": "system", "content": "system-prompt"},
            {"role": "user", "content": "round-1 plan " + "x" * 200},
            {"role": "assistant", "content": "round-1 finding " + "y" * 200},
            {"role": "user", "content": "round-2 plan"},
            {"role": "assistant", "content": "round-2 finding, keep me"},
        ],
    )
    event = AuditEvent(kind=EventKind.REASONING_ROUND, message="round")

    generated = await observer.handle(event, state)

    assert generated
    assert backend.calls == 1
    # System prompt preserved as the first message.
    assert state.messages[0]["content"] == "system-prompt"
    # A compression summary was inserted.
    assert any("历史上下文摘要" in m.get("content", "") and "SUMMARY" in m.get("content", "") for m in state.messages)
    # The recent round-2 finding survives.
    assert any("round-2 finding, keep me" in m.get("content", "") for m in state.messages)
    # Old verbose round-1 content was removed (replaced by the summary).
    assert not any("round-1 plan" in m.get("content", "") for m in state.messages)


async def test_context_compression_observer_skips_when_under_limit():
    """Below context_length, the observer does nothing."""
    settings = _FakeSettings()
    backend = _FakeCompressBackend("should-not-be-used")
    observer = ContextCompressionObserver(settings, backend)
    state = AgentObservationState(
        agent_id="a1",
        role="triage",
        system_prompt="sys",
        notes={},
        messages=[{"role": "system", "content": "sys"}, {"role": "user", "content": "short"}],
    )
    event = AuditEvent(kind=EventKind.REASONING_ROUND, message="round")
    generated = await observer.handle(event, state)
    assert not generated
    assert backend.calls == 0
