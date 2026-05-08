from __future__ import annotations

from dataclasses import dataclass, field

from app.models import AuditEvent, EventKind, Intervention, NoteEntry


@dataclass
class AgentObservationState:
    agent_id: str
    role: str
    system_prompt: str
    notes: dict[str, NoteEntry]
    messages: list[dict[str, str]] = field(default_factory=list)
    pending_interventions: list[Intervention] = field(default_factory=list)
    intervention_history: list[Intervention] = field(default_factory=list)
    runtime_events: list[AuditEvent] = field(default_factory=list)
    coordination_signatures: set[str] = field(default_factory=set)
    answered_message_ids: set[str] = field(default_factory=set)
    round_count: int = 0
    last_command_key: str | None = None
    consecutive_command_count: int = 0

    def append_intervention(self, source: str, instruction: str) -> Intervention:
        intervention = Intervention(source=source, instruction=instruction)
        self.pending_interventions.append(intervention)
        self.intervention_history.append(intervention)
        return intervention

    def consume_intervention_messages(self) -> list[dict[str, str]]:
        messages = [
            {"role": "system", "content": intervention.instruction}
            for intervention in self.pending_interventions
        ]
        self.pending_interventions.clear()
        return messages

    def reset_context(self) -> None:
        core_notes = [
            note.content
            for note in self.notes.values()
            if note.is_core and not note.invalidated
        ]
        rendered_notes = "\n".join(f"- {item}" for item in core_notes) or "- 暂无核心笔记"
        self.messages = [
            {"role": "system", "content": self.system_prompt},
            {
                "role": "system",
                "content": "上下文已被重置，仅保留以下核心笔记继续推理：\n" + rendered_notes,
            },
        ]


class ToolLoopObserver:
    def __init__(self, threshold: int) -> None:
        self.threshold = threshold

    async def handle(self, event: AuditEvent, state: AgentObservationState) -> list[AuditEvent]:
        if event.kind != EventKind.TOOL_INVOCATION:
            return []

        command_key = str(event.payload.get("command_key", "")).strip()
        if not command_key:
            return []

        if state.last_command_key == command_key:
            state.consecutive_command_count += 1
        else:
            state.last_command_key = command_key
            state.consecutive_command_count = 1

        if state.consecutive_command_count < self.threshold:
            return []

        state.consecutive_command_count = 0
        intervention = state.append_intervention(
            "tool-loop-guard",
            (
                f"检测到子代理连续重复调用命令 `{command_key}`。"
                "立即停止重复尝试，先总结失败原因，再切换分析路径或更换工具。"
            ),
        )
        return [
            AuditEvent(
                kind=EventKind.INTERVENTION_INJECTED,
                message="Tool loop guard injected an intervention",
                agent_id=state.agent_id,
                payload={
                    "command_key": command_key,
                    "source": intervention.source,
                },
            )
        ]


class NoteRecallObserver:
    def __init__(self, threshold: int) -> None:
        self.threshold = threshold

    async def handle(self, event: AuditEvent, state: AgentObservationState) -> list[AuditEvent]:
        if event.kind != EventKind.NOTE_RETRIEVAL:
            return []

        note_id = str(event.payload.get("note_id", "")).strip()
        note = state.notes.get(note_id)
        if note is None:
            return []

        note.retrieval_count += 1
        note.last_retrieved_at = event.created_at
        if note.retrieval_count < self.threshold:
            return []

        note.invalidated = True
        intervention = state.append_intervention(
            "note-recall-guard",
            (
                f"笔记 `{note_id}` 已被重复检索 {note.retrieval_count} 次，"
                "现已强制清除。后续必须重新验证相关假设，避免路径依赖。"
            ),
        )
        return [
            AuditEvent(
                kind=EventKind.NOTE_EVICTED,
                message="Repeatedly retrieved note was evicted",
                agent_id=state.agent_id,
                payload={"note_id": note_id, "source": note.source},
            ),
            AuditEvent(
                kind=EventKind.INTERVENTION_INJECTED,
                message="Note recall guard injected an intervention",
                agent_id=state.agent_id,
                payload={"note_id": note_id, "source": intervention.source},
            ),
        ]


class ContextWindowObserver:
    def __init__(self, threshold: int) -> None:
        self.threshold = threshold

    async def handle(self, event: AuditEvent, state: AgentObservationState) -> list[AuditEvent]:
        if event.kind != EventKind.REASONING_ROUND:
            return []

        state.round_count += 1
        if state.round_count <= self.threshold:
            return []

        state.round_count = 0
        state.reset_context()
        intervention = state.append_intervention(
            "context-reset-guard",
            "推理轮次超过安全阈值，已重置上下文。后续仅允许基于核心笔记继续推理。",
        )
        return [
            AuditEvent(
                kind=EventKind.CONTEXT_RESET,
                message="Context window was reset after excessive reasoning rounds",
                agent_id=state.agent_id,
                payload={"source": intervention.source},
            ),
            AuditEvent(
                kind=EventKind.INTERVENTION_INJECTED,
                message="Context reset guard injected an intervention",
                agent_id=state.agent_id,
                payload={"source": intervention.source},
            ),
        ]
