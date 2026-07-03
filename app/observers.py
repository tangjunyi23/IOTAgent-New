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


def estimate_token_count(messages: list[dict[str, str]]) -> int:
    """Estimate token count for an OpenAI-style message list.

    Vendor-agnostic: tries tiktoken (cl100k_base) if installed, else falls back
    to a char/4 heuristic. The char/4 fallback overestimates for CJK-heavy
    content, which is safe for a cap (compresses earlier rather than later).
    """
    total_chars = 0
    for message in messages:
        content = str(message.get("content") or "")
        total_chars += len(content) + 4  # 4 tokens framing overhead per message
    try:
        import tiktoken  # type: ignore[import-not-found]

        enc = tiktoken.get_encoding("cl100k_base")
        return sum(len(enc.encode(str(message.get("content") or ""))) + 4 for message in messages)
    except Exception:
        return total_chars // 4


class ContextCompressionObserver:
    """Compresses conversation history when token count exceeds context_length.

    Replaces older messages with an LLM-generated summary, keeping recent
    messages and core notes. The ContextWindowObserver (round-threshold) stays
    registered as a hard backstop. Requires an LLMBackend with compress_context.
    """

    def __init__(self, settings, llm_backend) -> None:
        self.settings = settings
        self.llm_backend = llm_backend
        self._compressing = False

    async def handle(self, event: AuditEvent, state: AgentObservationState) -> list[AuditEvent]:
        if event.kind != EventKind.REASONING_ROUND or self._compressing:
            return []
        token_count = estimate_token_count(state.messages)
        context_length = int(getattr(self.settings, "context_length", 500000) or 500000)
        if token_count <= context_length:
            return []
        self._compressing = True
        try:
            await self._compress_messages(state, token_count)
        finally:
            self._compressing = False
        return [
            AuditEvent(
                kind=EventKind.CONTEXT_RESET,
                message=f"Context compressed at {token_count} tokens",
                agent_id=state.agent_id,
                payload={"compressed": True, "tokens_before": token_count},
            ),
        ]

    async def _compress_messages(self, state: AgentObservationState, token_count: int) -> None:
        ratio = float(getattr(self.settings, "context_compression_ratio", 0.5) or 0.5)
        keep_tokens = int(int(getattr(self.settings, "context_length", 500000)) * ratio)
        # Walk backwards to find the split point: keep recent messages whose
        # cumulative token count is <= keep_tokens. Compress everything before.
        messages = state.messages
        if len(messages) <= 2:
            return  # nothing to compress
        keep_count = 0
        running = 0
        for idx in range(len(messages) - 1, -1, -1):
            running += estimate_token_count([messages[idx]])
            if running > keep_tokens:
                break
            keep_count = idx + 1
        keep_count = max(keep_count, 1)  # always keep at least the system prompt
        to_compress = messages[:keep_count]
        if not to_compress:
            return
        # Preserve the very first system prompt; compress the rest of the old block.
        first_system = messages[0] if messages[0].get("role") == "system" else None
        compress_target = to_compress[1:] if first_system else to_compress
        if not compress_target:
            return
        from app.model_router import ModelSelection

        compress_model = getattr(self.settings, "context_compress_model", None) or getattr(
            self.settings, "manager_regular_model", None
        )
        selection = ModelSelection(model=compress_model, route_reason="context-compression")
        compression_prompt = [
            {"role": "system", "content": "你是上下文压缩器。把以下子代理历史对话压缩成摘要，保留所有已验证事实、函数地址、exploit stage、阻塞和核心结论，不要丢失具体证据引用。"},
            {"role": "user", "content": "\n\n".join(
                f"[{m.get('role','')}]: {m.get('content','')}" for m in compress_target
            )},
        ]
        try:
            reply = await self.llm_backend.compress_context(
                messages=compression_prompt,
                selection=selection,
            )
            summary = (reply.content or "").strip() or "历史上下文已压缩，无可用摘要。"
        except Exception:
            # Compression failed — fall back to a hard reset to keep the agent alive.
            state.reset_context()
            return
        new_messages: list[dict[str, str]] = []
        if first_system:
            new_messages.append(first_system)
        new_messages.append({"role": "system", "content": f"历史上下文摘要：\n{summary}"})
        new_messages.extend(messages[keep_count:])
        state.messages = new_messages
