from __future__ import annotations

import asyncio
import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Awaitable, Callable

from app.config import Settings
from app.coordination import AgentMailbox
from app.events import EventBus
from app.llm import LLMBackend, create_llm_backend
from app.models import (
    AgentMessage,
    AuditEvent,
    CommandEvidence,
    EventKind,
    NoteEntry,
    SubAgentPayload,
    SubAgentResult,
    SubAgentStatus,
    TokenUsageSnapshot,
)
from app.observers import (
    AgentObservationState,
    ContextCompressionObserver,
    ContextWindowObserver,
    NoteRecallObserver,
    ToolLoopObserver,
)
from app.pwn_skill import PwnSkillPack
from app.target_utils import ensure_target_executable
from app.toolbox import BinaryToolbox

EventSink = Callable[[AuditEvent], Awaitable[None]]


class SubAgentWorker:
    def __init__(self, settings: Settings, llm_backend: LLMBackend | None = None) -> None:
        self.settings = settings
        self.llm_backend = llm_backend or create_llm_backend(settings)
        self.pwn_skill = PwnSkillPack(settings)
        self.toolbox = BinaryToolbox(settings)
        observers: list = [
            ToolLoopObserver(settings.loop_threshold),
            NoteRecallObserver(settings.note_recall_threshold),
            ContextWindowObserver(settings.round_reset_threshold),
        ]
        # Register the context-compression observer only when a real LLM backend
        # is available (MissingLLMBackend raises on compress_context and would
        # never produce useful compression).
        if "Missing" not in type(self.llm_backend).__name__:
            observers.append(ContextCompressionObserver(settings, self.llm_backend))
        self.event_bus = EventBus(observers=observers)
        # Per-(session, role) persistent conversation state across manager rounds.
        # Keyed by (session_id, role) — NOT task.id, since each round mints a new
        # task UUID. Lets round N+1 continue the same LLM conversation as round N
        # instead of starting fresh (fixes cross-round repetition).
        self._role_state_cache: dict[tuple[str, str], AgentObservationState] = {}

    def clear_role_state(self, session_id: str) -> None:
        for key in [k for k in self._role_state_cache if k[0] == session_id]:
            self._role_state_cache.pop(key, None)

    def _build_fresh_state(self, payload: SubAgentPayload) -> AgentObservationState:
        seeded_notes = {
            note.id: note.model_copy(deep=True)
            for note in payload.core_notes
        }
        for memory in payload.shared_memory:
            note_id = f"memory:{memory.id}"
            seeded_notes[note_id] = NoteEntry(
                id=note_id,
                content=memory.content,
                source=f"shared-memory:{memory.category}",
                is_core=True,
            )
        for index, brief in enumerate(payload.task.continuation_brief):
            note_id = f"continuation:{payload.task.id}:{index}"
            seeded_notes[note_id] = NoteEntry(
                id=note_id,
                content=brief,
                source="manager:continuation",
                is_core=True,
            )
        state = AgentObservationState(
            agent_id=payload.task.id,
            role=payload.task.role,
            system_prompt=self._build_system_prompt(
                payload.task.role,
                payload.objective,
                continuation_brief=payload.task.continuation_brief,
                available_tool_ids=payload.available_tool_ids,
                reused_tool_ids=payload.task.reused_tool_ids,
            ),
            notes=seeded_notes,
        )
        for note in self.pwn_skill.build_role_notes(payload.task.role):
            note_id = f"{note.source}:{payload.task.role}:{len(state.notes)}"
            state.notes[note_id] = NoteEntry(
                id=note_id,
                content=note.content,
                source=note.source,
                is_core=True,
            )
        state.reset_context()
        return state

    def _refresh_state_for_continuation(
        self,
        state: AgentObservationState,
        payload: SubAgentPayload,
    ) -> None:
        """Merge a new round's notes/brief into an existing persistent state
        without wiping message history. Notes are idempotent by id."""
        for note in payload.core_notes:
            state.notes[note.id] = note.model_copy(deep=True)
        for memory in payload.shared_memory:
            note_id = f"memory:{memory.id}"
            state.notes[note_id] = NoteEntry(
                id=note_id,
                content=memory.content,
                source=f"shared-memory:{memory.category}",
                is_core=True,
            )
        for index, brief in enumerate(payload.task.continuation_brief):
            note_id = f"continuation:{payload.task.id}:{index}"
            state.notes[note_id] = NoteEntry(
                id=note_id,
                content=brief,
                source="manager:continuation",
                is_core=True,
            )
        # New task UUID each round; update agent_id so tool evidence is tagged correctly.
        state.agent_id = payload.task.id
        # Cap retained messages to bound memory (keep most recent ~2 rounds).
        if len(state.messages) > 80:
            state.messages = state.messages[-80:]
        # Mark the round boundary so the LLM knows it's a continuation, not a reset.
        state.messages.append(
            {
                "role": "system",
                "content": (
                    f"Manager 第 {payload.task.round_index} 轮继续；基于上文已验证证据推进，"
                    "不要重复已完成的基础工具，不要重复已广播过的事实。"
                ),
            }
        )

    async def execute(
        self,
        payload: SubAgentPayload,
        event_sink: EventSink | None = None,
    ) -> SubAgentResult:
        cache_key = (payload.session_id, payload.task.role)
        state: AgentObservationState | None = None
        if payload.continue_role_session:
            state = self._role_state_cache.get(cache_key)
        if state is None:
            state = self._build_fresh_state(payload)
            self._role_state_cache[cache_key] = state
        else:
            self._refresh_state_for_continuation(state, payload)
        mailbox = AgentMailbox(payload.coordination_dir) if payload.coordination_dir else None
        seen_message_ids: set[str] = set()
        plan_selection = self._selection_for_task_phase(payload.task, phase="plan")
        discussion_selection = self._selection_for_task_phase(payload.task, phase="discussion")
        summary_selection = self._selection_for_task_phase(payload.task, phase="summary")
        plan_summary: str | None = None
        evidence = [item.model_copy(deep=True) for item in payload.seed_evidence]
        token_usage = TokenUsageSnapshot()

        async def publish(event: AuditEvent) -> None:
            if payload.event_stream_path is not None:
                await asyncio.to_thread(self._append_event_line, payload.event_stream_path, event)
            if event_sink is not None:
                await event_sink(event)
            state.runtime_events.append(event)
            generated = await self.event_bus.publish(event, state)
            for generated_event in generated:
                if payload.event_stream_path is not None:
                    await asyncio.to_thread(self._append_event_line, payload.event_stream_path, generated_event)
                if event_sink is not None:
                    await event_sink(generated_event)
            state.runtime_events.extend(generated)

        async def record_llm_usage(stage: str, reply, selection) -> None:
            token_usage.prompt_tokens += int(getattr(reply, "prompt_tokens", 0) or 0)
            token_usage.completion_tokens += int(getattr(reply, "completion_tokens", 0) or 0)
            token_usage.total_tokens += int(getattr(reply, "total_tokens", 0) or 0)
            token_usage.reasoning_tokens += int(getattr(reply, "reasoning_tokens", 0) or 0)
            token_usage.cached_tokens += int(getattr(reply, "cached_tokens", 0) or 0)
            token_usage.llm_calls += int(getattr(reply, "llm_calls", 0) or 0)
            await publish(
                AuditEvent(
                    kind=EventKind.LLM_USAGE_RECORDED,
                    message=f"Sub-agent {payload.task.role} recorded {stage} token usage",
                    agent_id=payload.task.id,
                    payload={
                        "stage": stage,
                        "model": getattr(reply, "model", None) or selection.model,
                        "route_reason": selection.route_reason,
                        "prompt_tokens": int(getattr(reply, "prompt_tokens", 0) or 0),
                        "completion_tokens": int(getattr(reply, "completion_tokens", 0) or 0),
                        "total_tokens": int(getattr(reply, "total_tokens", 0) or 0),
                        "reasoning_tokens": int(getattr(reply, "reasoning_tokens", 0) or 0),
                        "cached_tokens": int(getattr(reply, "cached_tokens", 0) or 0),
                        "llm_calls": int(getattr(reply, "llm_calls", 0) or 0),
                    },
                )
            )

        try:
            await publish(
                AuditEvent(
                    kind=EventKind.REASONING_ROUND,
                    message="Sub-agent started planning round",
                    agent_id=payload.task.id,
                )
            )
            if payload.task.reused_tool_ids:
                await publish(
                    AuditEvent(
                        kind=EventKind.REASONING_ROUND,
                        message="Sub-agent loaded shared memory and reused prior tool evidence",
                        agent_id=payload.task.id,
                        payload={
                            "reused_tool_ids": payload.task.reused_tool_ids,
                            "shared_memory_count": len(payload.shared_memory),
                        },
                    )
                )
            core_note_text = await self._retrieve_core_notes(state, publish)
            plan_reply = await self.llm_backend.draft_plan(
                task=payload.task,
                core_notes=core_note_text,
                selection=plan_selection,
                interventions=[item["content"] for item in state.consume_intervention_messages()],
                available_tools=self._tool_capabilities_for_payload(payload),
            )
            await record_llm_usage("plan", plan_reply, plan_selection)
            plan_summary = plan_reply.content
            state.messages.append({"role": "assistant", "content": plan_reply.content})
            await self._publish_peer_message(
                payload=payload,
                state=state,
                mailbox=mailbox,
                seen_message_ids=seen_message_ids,
                stage="plan",
                message_kind="plan",
                topic="初始分工",
                recipients=payload.task.collaboration_targets or payload.peer_roles,
                requires_response=False,
                content=self._build_plan_coordination_note(payload.task.role, plan_reply.content),
                publish=publish,
                wait_for_peers=payload.peer_count > 0,
            )

            try:
                evidence = await self.toolbox.collect(
                    payload.task.role,
                    payload.target_path,
                    publish,
                    existing_evidence=evidence,
                )
            except TypeError:
                collected = await self.toolbox.collect(
                    payload.task.role,
                    payload.target_path,
                    publish,
                )
                evidence = evidence + collected
            evidence = await self._run_collaboration_cycles(
                payload=payload,
                state=state,
                evidence=evidence,
                publish=publish,
                mailbox=mailbox,
                seen_message_ids=seen_message_ids,
                selection=discussion_selection,
                record_llm_usage=record_llm_usage,
            )

            await publish(
                AuditEvent(
                    kind=EventKind.REASONING_ROUND,
                    message="Sub-agent entered synthesis round",
                    agent_id=payload.task.id,
                )
            )
            if mailbox is not None:
                synthesis_messages = await self._ingest_peer_messages(
                    payload=payload,
                    state=state,
                    mailbox=mailbox,
                    seen_message_ids=seen_message_ids,
                    publish=publish,
                    wait_for_peers=False,
                )
                response_message = self._build_response_coordination_message(
                    payload,
                    evidence,
                    synthesis_messages,
                    state,
                )
                if response_message is not None:
                    await self._publish_peer_message(
                        payload=payload,
                        state=state,
                        mailbox=mailbox,
                        seen_message_ids=seen_message_ids,
                        stage="discussion",
                        message_kind="answer",
                        topic=response_message["topic"],
                        recipients=response_message["recipients"],
                        requires_response=False,
                        in_reply_to=response_message["in_reply_to"],
                        content=response_message["content"],
                        publish=publish,
                        wait_for_peers=False,
                    )
            core_note_text = await self._retrieve_core_notes(state, publish)
            final_reply = await self.llm_backend.finalize_analysis(
                task=payload.task,
                core_notes=core_note_text,
                evidence=evidence,
                plan=plan_reply.content,
                selection=summary_selection,
                interventions=[item["content"] for item in state.consume_intervention_messages()],
                available_tools=self._tool_capabilities_for_payload(payload),
            )
            await record_llm_usage("summary", final_reply, summary_selection)
            state.messages.append({"role": "assistant", "content": final_reply.content})
            await self._publish_peer_message(
                payload=payload,
                state=state,
                mailbox=mailbox,
                seen_message_ids=seen_message_ids,
                stage="summary",
                message_kind="summary",
                topic="最终结论",
                recipients=payload.task.collaboration_targets or payload.peer_roles,
                requires_response=False,
                content=self._build_summary_coordination_note(payload.task.role, final_reply.content),
                publish=publish,
                wait_for_peers=False,
            )
            evidence, support_updated = await self._run_post_summary_support(
                payload=payload,
                state=state,
                evidence=evidence,
                final_reply=final_reply,
                plan=plan_reply.content,
                publish=publish,
                mailbox=mailbox,
                seen_message_ids=seen_message_ids,
                selection=discussion_selection,
                record_llm_usage=record_llm_usage,
            )
            if support_updated:
                refreshed_reply = await self._refresh_summary_after_support(
                    payload=payload,
                    state=state,
                    evidence=evidence,
                    plan=plan_reply.content,
                    selection=summary_selection,
                    publish=publish,
                    mailbox=mailbox,
                    seen_message_ids=seen_message_ids,
                    previous_reply=final_reply,
                    record_llm_usage=record_llm_usage,
                )
                if refreshed_reply is not None:
                    final_reply = refreshed_reply
            await publish(
                AuditEvent(
                    kind=EventKind.SUBAGENT_COMPLETED,
                    message=f"Sub-agent {payload.task.role} completed",
                    agent_id=payload.task.id,
                )
            )
            promoted_notes = self._extract_promoted_notes(final_reply.content)
            return SubAgentResult(
                task_id=payload.task.id,
                status=SubAgentStatus.COMPLETED,
                plan_summary=plan_reply.content,
                summary=final_reply.content,
                token_usage=token_usage,
                evidence=evidence,
                interventions=state.intervention_history,
                promoted_notes=promoted_notes,
                events=state.runtime_events,
                container_id=payload.task.container_id,
            )
        except Exception as exc:
            await publish(
                AuditEvent(
                    kind=EventKind.SESSION_FAILED,
                    message=f"Sub-agent failed: {exc}",
                    agent_id=payload.task.id,
                )
            )
            return SubAgentResult(
                task_id=payload.task.id,
                status=SubAgentStatus.FAILED,
                plan_summary=plan_summary,
                token_usage=token_usage,
                evidence=evidence,
                error=str(exc),
                interventions=state.intervention_history,
                events=state.runtime_events,
                container_id=payload.task.container_id,
            )

    async def _run_collaboration_cycles(
        self,
        *,
        payload: SubAgentPayload,
        state: AgentObservationState,
        evidence: list[CommandEvidence],
        publish: EventSink,
        mailbox: AgentMailbox | None,
        seen_message_ids: set[str],
        selection,
        record_llm_usage,
    ) -> list[CommandEvidence]:
        collected = list(evidence)
        follow_up_round = 0
        max_rounds = max(4, self.settings.agent_discussion_max_rounds)
        if payload.task.role in {"static-analysis", "dynamic-analysis", "exploitability-review", "exploit-strategy"}:
            max_rounds += 2
        while True:
            phase_label = "初始证据阶段" if follow_up_round == 0 else f"证据细化阶段 {follow_up_round}"
            await publish(
                AuditEvent(
                    kind=EventKind.REASONING_ROUND,
                    message=f"Sub-agent entered {phase_label}",
                    agent_id=payload.task.id,
                    payload={"phase_index": follow_up_round, "phase_label": phase_label},
                )
            )
            incoming_messages: list[AgentMessage] = []
            if mailbox is not None:
                incoming_messages = await self._ingest_peer_messages(
                    payload=payload,
                    state=state,
                    mailbox=mailbox,
                    seen_message_ids=seen_message_ids,
                    publish=publish,
                    wait_for_peers=payload.peer_count > 0 and follow_up_round == 0,
                )

                if follow_up_round == 0 or incoming_messages or self._has_actionable_blockers(collected):
                    collaboration_reply = await self.llm_backend.draft_collaboration(
                        task=payload.task,
                        core_notes=[note.content for note in self._select_retrievable_notes(state, limit=12)],
                        evidence=collected,
                        peer_messages=self._render_peer_messages_for_llm(incoming_messages),
                        selection=selection,
                        interventions=[item["content"] for item in state.consume_intervention_messages()],
                        manager_plan_summary=payload.manager_plan_summary,
                        phase_label=phase_label,
                        available_tools=self._tool_capabilities_for_payload(payload),
                    )
                    await record_llm_usage("collaboration", collaboration_reply, selection)
                    state.messages.append({"role": "assistant", "content": collaboration_reply.content})
                    await self._publish_collaboration_messages(
                        payload=payload,
                        state=state,
                        mailbox=mailbox,
                        seen_message_ids=seen_message_ids,
                        evidence=collected,
                        incoming_messages=incoming_messages,
                        discussion_content=collaboration_reply.content,
                        phase_label=phase_label,
                        publish=publish,
                    )

            if follow_up_round >= max_rounds:
                break

            requests = self.toolbox.plan_follow_up(
                payload.task.role,
                collected,
                follow_up_round,
                peer_notes=self._peer_note_contents(state),
            )
            if not requests:
                break
            await publish(
                AuditEvent(
                    kind=EventKind.REASONING_ROUND,
                    message=f"Sub-agent entered evidence refinement round {follow_up_round + 1}",
                    agent_id=payload.task.id,
                    payload={
                        "round": follow_up_round + 1,
                        "tools": [request.command_id for request in requests],
                    },
                )
            )
            follow_up_evidence = await self.toolbox.collect_follow_up(payload.target_path, requests, publish)
            collected.extend(follow_up_evidence)
            follow_up_round += 1
        return collected

    async def _run_post_summary_support(
        self,
        *,
        payload: SubAgentPayload,
        state: AgentObservationState,
        evidence: list[CommandEvidence],
        final_reply,
        plan: str,
        publish: EventSink,
        mailbox: AgentMailbox | None,
        seen_message_ids: set[str],
        selection,
        record_llm_usage,
    ) -> tuple[list[CommandEvidence], bool]:
        if mailbox is None or payload.peer_count <= 0:
            return evidence, False

        expected_summary_roles = {role for role in payload.peer_roles if role and role != payload.task.role}
        if not expected_summary_roles:
            return evidence, False

        collected = list(evidence)
        updated = False
        received_summary_roles: set[str] = set()
        support_round = 0
        deadline = asyncio.get_running_loop().time() + max(
            self.settings.agent_coordination_timeout_seconds,
            float(self.settings.tool_timeout_seconds),
        )

        while received_summary_roles != expected_summary_roles:
            if asyncio.get_running_loop().time() >= deadline:
                break

            incoming_messages = await self._ingest_peer_messages(
                payload=payload,
                state=state,
                mailbox=mailbox,
                seen_message_ids=seen_message_ids,
                publish=publish,
                wait_for_peers=True,
            )
            if not incoming_messages:
                continue

            updated = True
            support_round += 1
            for message in incoming_messages:
                if message.message_kind == "summary" and message.sender_role:
                    received_summary_roles.add(message.sender_role)

            await publish(
                AuditEvent(
                    kind=EventKind.REASONING_ROUND,
                    message=f"Sub-agent entered standby support round {support_round}",
                    agent_id=payload.task.id,
                    payload={
                        "phase_label": f"待命支援阶段 {support_round}",
                        "support_round": support_round,
                        "received_summary_roles": sorted(received_summary_roles),
                        "pending_summary_roles": sorted(expected_summary_roles - received_summary_roles),
                    },
                )
            )

            requests = self.toolbox.plan_follow_up(
                payload.task.role,
                collected,
                self.settings.agent_discussion_max_rounds + support_round,
                peer_notes=self._peer_note_contents(state),
            )
            if requests:
                follow_up_evidence = await self.toolbox.collect_follow_up(payload.target_path, requests, publish)
                if follow_up_evidence:
                    collected.extend(follow_up_evidence)

            if any(message.requires_response for message in incoming_messages) or self._has_actionable_blockers(collected):
                collaboration_reply = await self.llm_backend.draft_collaboration(
                    task=payload.task,
                    core_notes=[note.content for note in self._select_retrievable_notes(state, limit=12)],
                    evidence=collected,
                    peer_messages=self._render_peer_messages_for_llm(incoming_messages),
                    selection=selection,
                    interventions=[item["content"] for item in state.consume_intervention_messages()],
                    manager_plan_summary=payload.manager_plan_summary,
                    phase_label=f"待命支援阶段 {support_round}",
                    available_tools=self._tool_capabilities_for_payload(payload),
                )
                await record_llm_usage("support-collaboration", collaboration_reply, selection)
                state.messages.append({"role": "assistant", "content": collaboration_reply.content})
                await self._publish_collaboration_messages(
                    payload=payload,
                    state=state,
                    mailbox=mailbox,
                    seen_message_ids=seen_message_ids,
                    evidence=collected,
                    incoming_messages=incoming_messages,
                    discussion_content=collaboration_reply.content,
                    phase_label=f"待命支援阶段 {support_round}",
                    publish=publish,
                )

        return collected, updated

    async def _refresh_summary_after_support(
        self,
        *,
        payload: SubAgentPayload,
        state: AgentObservationState,
        evidence: list[CommandEvidence],
        plan: str,
        selection,
        publish: EventSink,
        mailbox: AgentMailbox | None,
        seen_message_ids: set[str],
        previous_reply,
        record_llm_usage,
    ):
        try:
            core_note_text = await self._retrieve_core_notes(state, publish)
            refreshed_reply = await self.llm_backend.finalize_analysis(
                task=payload.task,
                core_notes=core_note_text,
                evidence=evidence,
                plan=plan,
                selection=selection,
                interventions=[item["content"] for item in state.consume_intervention_messages()],
                available_tools=self._tool_capabilities_for_payload(payload),
            )
            await record_llm_usage("summary-refresh", refreshed_reply, selection)
        except Exception as exc:
            await publish(
                AuditEvent(
                    kind=EventKind.REASONING_ROUND,
                    message="Sub-agent kept prior summary after standby refresh failed",
                    agent_id=payload.task.id,
                    payload={"error": str(exc)},
                )
            )
            return None

        if refreshed_reply.content.strip() != previous_reply.content.strip():
            state.messages.append({"role": "assistant", "content": refreshed_reply.content})
            await self._publish_peer_message(
                payload=payload,
                state=state,
                mailbox=mailbox,
                seen_message_ids=seen_message_ids,
                stage="summary",
                message_kind="summary",
                topic="更新结论",
                recipients=payload.task.collaboration_targets or payload.peer_roles,
                requires_response=False,
                content=self._build_summary_coordination_note(payload.task.role, refreshed_reply.content),
                publish=publish,
                wait_for_peers=False,
            )
        return refreshed_reply

    def _append_event_line(self, output_path: str, event: AuditEvent) -> None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.model_dump(mode="json"), ensure_ascii=False) + "\n")

    async def _retrieve_core_notes(
        self,
        state: AgentObservationState,
        publish,
    ) -> list[str]:
        retrieved: list[str] = []
        for note in self._select_retrievable_notes(state, limit=12):
            if note.invalidated:
                continue
            await publish(
                AuditEvent(
                    kind=EventKind.NOTE_RETRIEVAL,
                    message=f"Retrieved note from {note.source}",
                    agent_id=state.agent_id,
                    payload={"note_id": note.id, "source": note.source},
                )
            )
            if not note.invalidated:
                retrieved.append(note.content)
        return retrieved

    def _select_retrievable_notes(
        self,
        state: AgentObservationState,
        *,
        limit: int,
    ) -> list[NoteEntry]:
        weighted: list[tuple[int, NoteEntry]] = []
        for note in state.notes.values():
            if note.invalidated:
                continue
            weighted.append((self._note_priority(note), note))
        weighted.sort(
            key=lambda item: (
                item[0],
                item[1].retrieval_count * -1,
                item[1].created_at,
            ),
            reverse=True,
        )
        selected: list[NoteEntry] = []
        seen_contents: set[str] = set()
        for _, note in weighted:
            normalized = re.sub(r"\s+", " ", note.content).strip()
            if not normalized or normalized in seen_contents:
                continue
            seen_contents.add(normalized)
            selected.append(note)
            if len(selected) >= limit:
                break
        return selected

    def _note_priority(self, note: NoteEntry) -> int:
        priority = 0
        if note.is_core:
            priority += 120
        if note.source.startswith("shared-memory:fixed"):
            priority += 110
        elif note.source.startswith("shared-memory:"):
            priority += 95
        elif note.source.startswith("manager"):
            priority += 88
        elif note.source.startswith("analyst"):
            priority += 80
        elif note.source.startswith("peer:"):
            priority += 52
        elif note.source.startswith("skill:"):
            priority += 40
        priority -= min(note.retrieval_count, 8) * 4
        return priority

    def _tool_capabilities_for_payload(self, payload: SubAgentPayload):
        available = set(payload.available_tool_ids or [])
        return [item for item in self.toolbox.list_capabilities() if item.tool_id in available]

    def _build_system_prompt(
        self,
        role: str,
        objective: str,
        *,
        continuation_brief: list[str] | None = None,
        available_tool_ids: list[str] | None = None,
        reused_tool_ids: list[str] | None = None,
    ) -> str:
        continuation_text = "；".join(item.strip() for item in (continuation_brief or []) if item and item.strip())
        available_tools_text = ", ".join(item for item in (available_tool_ids or []) if item) or "无"
        reused_tools_text = ", ".join(item for item in (reused_tool_ids or []) if item) or "无"
        return (
            f"你是漏洞审计平台中的 `{role}` 子代理。目标：{objective}。"
            "每轮显式继承上一轮已完成工具结果、共享记忆和已证明 exploit stage，不把本轮当从零开始；已覆盖的基础事实不重复分析。"
            f"当前可用工具仅限：{available_tools_text}；不可用工具改走旁路证据，不反复请求同一 unavailable 工具。"
            f"本轮已复用历史工具：{reused_tools_text}。"
            "已有崩溃证据时不要把再次验证崩溃当终点，必须推进到 信息泄露 / 栈覆盖 / canary 命中 / RIP 可控 / RCE / getshell / flag 的某一级；canary/PIE/Full RELRO 阻断时写清当前边界与缺步。"
            "若上下文已有某条事实，不在协作消息里重复广播，只广播本轮新增证据或阻塞。"
            + (f"跨轮延续约束：{continuation_text}。" if continuation_text else "")
        )

    async def _publish_peer_message(
        self,
        *,
        payload: SubAgentPayload,
        state: AgentObservationState,
        mailbox: AgentMailbox | None,
        seen_message_ids: set[str],
        stage: str,
        message_kind: str,
        topic: str | None,
        recipients: list[str] | None,
        requires_response: bool,
        content: str,
        publish: EventSink,
        wait_for_peers: bool,
        in_reply_to: str | None = None,
    ) -> AgentMessage | None:
        if mailbox is None or not content.strip():
            return None
        signature = self._coordination_signature(stage, message_kind, topic, recipients, content, in_reply_to)
        if signature in state.coordination_signatures:
            return None
        state.coordination_signatures.add(signature)

        message = await asyncio.to_thread(
            mailbox.publish,
            session_id=payload.session_id,
            sender_task_id=payload.task.id,
            sender_role=payload.task.role,
            stage=stage,
            message_kind=message_kind,
            topic=topic,
            recipients=recipients,
            requires_response=requires_response,
            in_reply_to=in_reply_to,
            content=content,
        )
        await publish(
            AuditEvent(
                kind=EventKind.AGENT_MESSAGE_SENT,
                message=self._build_sent_event_message(payload.task.role, stage, message_kind, recipients),
                agent_id=payload.task.id,
                payload={
                    "message_id": message.id,
                    "stage": stage,
                    "sender_role": payload.task.role,
                    "message_kind": message_kind,
                    "topic": topic,
                    "recipients": recipients or [],
                    "requires_response": requires_response,
                    "in_reply_to": in_reply_to,
                    "content": content,
                    "content_preview": self._compact_coordination_text(content, limit=220),
                },
            )
        )
        if wait_for_peers:
            await self._ingest_peer_messages(
                payload=payload,
                state=state,
                mailbox=mailbox,
                seen_message_ids=seen_message_ids,
                publish=publish,
                wait_for_peers=True,
            )
        return message

    async def _publish_collaboration_messages(
        self,
        *,
        payload: SubAgentPayload,
        state: AgentObservationState,
        mailbox: AgentMailbox | None,
        seen_message_ids: set[str],
        evidence: list[CommandEvidence],
        incoming_messages: list[AgentMessage],
        discussion_content: str,
        phase_label: str,
        publish: EventSink,
    ) -> None:
        if mailbox is None:
            return

        stage = "evidence" if phase_label.startswith("初始") else "discussion"
        targets = payload.task.collaboration_targets or payload.peer_roles
        update_content = self._compact_coordination_text(discussion_content, limit=520)
        update_topic = self._derive_coordination_topic(evidence, self._peer_note_contents(state))
        if update_content:
            await self._publish_peer_message(
                payload=payload,
                state=state,
                mailbox=mailbox,
                seen_message_ids=seen_message_ids,
                stage=stage,
                message_kind="update",
                topic=update_topic,
                recipients=targets,
                requires_response=False,
                content=update_content,
                publish=publish,
                wait_for_peers=False,
            )

        response_message = self._build_response_coordination_message(payload, evidence, incoming_messages, state)
        if response_message is not None:
            await self._publish_peer_message(
                payload=payload,
                state=state,
                mailbox=mailbox,
                seen_message_ids=seen_message_ids,
                stage="discussion",
                message_kind="answer",
                topic=response_message["topic"],
                recipients=response_message["recipients"],
                requires_response=False,
                in_reply_to=response_message["in_reply_to"],
                content=response_message["content"],
                publish=publish,
                wait_for_peers=False,
            )
            for message_id in response_message.get("answered_message_ids", []):
                if message_id:
                    state.answered_message_ids.add(str(message_id))

        blocker_message = self._build_blocker_coordination_message(payload, evidence, state)
        if blocker_message is not None:
            await self._publish_peer_message(
                payload=payload,
                state=state,
                mailbox=mailbox,
                seen_message_ids=seen_message_ids,
                stage="discussion",
                message_kind="question",
                topic=blocker_message["topic"],
                recipients=blocker_message["recipients"],
                requires_response=True,
                content=blocker_message["content"],
                publish=publish,
                wait_for_peers=True,
            )

    async def _ingest_peer_messages(
        self,
        *,
        payload: SubAgentPayload,
        state: AgentObservationState,
        mailbox: AgentMailbox,
        seen_message_ids: set[str],
        publish: EventSink,
        wait_for_peers: bool,
    ) -> list[AgentMessage]:
        deadline = asyncio.get_running_loop().time() + self.settings.agent_coordination_timeout_seconds
        while True:
            messages = await asyncio.to_thread(
                mailbox.drain_for_peer,
                recipient_task_id=payload.task.id,
                recipient_role=payload.task.role,
                seen_message_ids=seen_message_ids,
            )
            if messages:
                for message in messages:
                    note_id = f"peer-{message.id}"
                    topic_suffix = f"/{message.topic}" if message.topic else ""
                    if note_id not in state.notes:
                        state.notes[note_id] = NoteEntry(
                            id=note_id,
                            content=f"[来自{message.sender_role}/{message.stage}/{message.message_kind}{topic_suffix}] {message.content}",
                            source=f"peer:{message.sender_role}",
                            is_core=False,
                        )
                    await publish(
                        AuditEvent(
                            kind=EventKind.AGENT_MESSAGE_RECEIVED,
                            message=self._build_received_event_message(payload.task.role, message),
                            agent_id=payload.task.id,
                            payload={
                                "message_id": message.id,
                                "stage": message.stage,
                                "sender_role": message.sender_role,
                                "message_kind": message.message_kind,
                                "topic": message.topic,
                                "recipients": message.recipients,
                                "requires_response": message.requires_response,
                                "in_reply_to": message.in_reply_to,
                                "content": message.content,
                                "content_preview": self._compact_coordination_text(message.content, limit=220),
                            },
                        )
                    )
                return messages

            if not wait_for_peers or payload.peer_count <= 0:
                return []
            if asyncio.get_running_loop().time() >= deadline:
                return []
            await asyncio.sleep(0.05)

    def _build_sent_event_message(
        self,
        role: str,
        stage: str,
        message_kind: str,
        recipients: list[str] | None,
    ) -> str:
        recipient_text = ", ".join(recipients or []) or "all peers"
        if message_kind == "question":
            return f"Sub-agent {role} asked peers for help during {stage} ({recipient_text})"
        if message_kind == "answer":
            return f"Sub-agent {role} answered peer questions during {stage} ({recipient_text})"
        return f"Sub-agent {role} shared a {stage} {message_kind} ({recipient_text})"

    def _build_received_event_message(self, role: str, message: AgentMessage) -> str:
        if message.message_kind == "question":
            return f"Sub-agent {role} received a peer question from {message.sender_role}"
        if message.message_kind == "answer":
            return f"Sub-agent {role} received a peer answer from {message.sender_role}"
        return f"Sub-agent {role} received a {message.stage} update from {message.sender_role}"

    def _render_peer_messages_for_llm(self, messages: list[AgentMessage]) -> list[str]:
        rendered: list[str] = []
        for message in messages:
            topic = f" topic={message.topic}" if message.topic else ""
            rendered.append(
                f"{message.sender_role}/{message.stage}/{message.message_kind}{topic}: {message.content}"
            )
        return rendered

    def _peer_note_contents(self, state: AgentObservationState) -> list[str]:
        contents: list[str] = []
        for note in state.notes.values():
            if note.invalidated or not note.source.startswith("peer:"):
                continue
            contents.append(note.content)
        return contents

    def _derive_coordination_topic(self, evidence: list[CommandEvidence], peer_notes: list[str]) -> str:
        blockers = [item.command_id for item in evidence[-4:] if item.status in {"failed", "timeout", "unavailable"}]
        if blockers:
            return f"阻塞协查:{'/'.join(blockers[:2])}"
        focus = self._focus_function_brief(evidence, peer_notes)
        if focus:
            return f"函数协查:{focus}"
        completed = [item.command_id for item in evidence[-3:] if item.status == "completed"]
        if completed:
            return f"证据进展:{'/'.join(completed[:2])}"
        return "阶段进展"

    def _focus_function_brief(self, evidence: list[CommandEvidence], peer_notes: list[str]) -> str:
        identify = getattr(self.toolbox, "_identify_focus_functions", None)
        if not callable(identify):
            return ""
        try:
            functions = identify(evidence, peer_notes=peer_notes)
        except TypeError:
            functions = identify(evidence)
        labels: list[str] = []
        for item in functions[:2]:
            address = f"@0x{item.address:x}" if getattr(item, "address", 0) else ""
            labels.append(f"{item.name}{address}")
        return ", ".join(labels)

    def _build_response_coordination_message(
        self,
        payload: SubAgentPayload,
        evidence: list[CommandEvidence],
        incoming_messages: list[AgentMessage],
        state: AgentObservationState,
    ) -> dict[str, object] | None:
        pending_questions = [
            message
            for message in incoming_messages
            if (
                message.requires_response
                and message.sender_role != payload.task.role
                and message.id not in state.answered_message_ids
            )
        ]
        if not pending_questions:
            return None
        recipients = list(dict.fromkeys(message.sender_role for message in pending_questions))
        topic = pending_questions[0].topic or "协查回应"
        focus = self._focus_function_brief(evidence, self._peer_note_contents(state))
        evidence_summary = self._build_evidence_coordination_note(payload.task.role, evidence)
        content = f"{payload.task.role} 回应协查：{evidence_summary}"
        if focus:
            content += f"；当前重点函数 {focus}"
        return {
            "topic": topic,
            "recipients": recipients,
            "content": content,
            "in_reply_to": pending_questions[0].id if len(pending_questions) == 1 else None,
            "answered_message_ids": [message.id for message in pending_questions],
        }

    def _build_blocker_coordination_message(
        self,
        payload: SubAgentPayload,
        evidence: list[CommandEvidence],
        state: AgentObservationState,
    ) -> dict[str, object] | None:
        if payload.peer_count <= 0:
            return None
        blockers = [item for item in evidence[-4:] if item.status in {"failed", "timeout", "unavailable"}]
        if not blockers:
            return None
        blocker_text = "; ".join(f"{item.command_id}={item.status}" for item in blockers[:3])
        focus = self._focus_function_brief(evidence, self._peer_note_contents(state))
        focus_text = f" 当前重点函数 {focus}。" if focus else ""
        return {
            "topic": self._derive_coordination_topic(evidence, self._peer_note_contents(state)),
            "recipients": payload.task.collaboration_targets or payload.peer_roles,
            "content": (
                f"{payload.task.role} 遇到阻塞：{blocker_text}。"
                f"请同伴结合你们已完成的工具补齐对应函数级证据。{focus_text}"
            ).strip(),
        }

    def _build_plan_coordination_note(self, role: str, plan_content: str) -> str:
        summary = self._compact_coordination_text(plan_content, limit=360)
        return f"{role} 规划摘要：{summary}" if summary else ""

    def _build_evidence_coordination_note(self, role: str, evidence: list) -> str:
        completed = [f"{item.command_id}={item.status}" for item in evidence[:8]]
        if not completed:
            return ""
        return f"{role} 证据进展：{'; '.join(completed)}"

    def _build_summary_coordination_note(self, role: str, summary_content: str) -> str:
        summary = self._compact_coordination_text(summary_content, limit=480)
        return f"{role} 结论摘要：{summary}" if summary else ""

    def _compact_coordination_text(self, content: str, *, limit: int) -> str:
        lines = [
            line.strip()
            for line in content.splitlines()
            if line.strip() and not line.strip().startswith(("##", "###"))
        ]
        text = " ".join(lines)
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) <= limit:
            return text
        return text[: limit - 1].rstrip() + "…"

    def _coordination_signature(
        self,
        stage: str,
        message_kind: str,
        topic: str | None,
        recipients: list[str] | None,
        content: str,
        in_reply_to: str | None,
    ) -> str:
        normalized_content = self._compact_coordination_text(content, limit=320)
        recipient_key = ",".join(sorted(recipients or []))
        return "|".join(
            [
                stage,
                message_kind,
                topic or "",
                recipient_key,
                in_reply_to or "",
                normalized_content,
            ]
        )

    def _selection_for_task_phase(self, task, *, phase: str):
        from app.model_router import ModelSelection

        if phase == "plan":
            model = task.planning_model or task.model
        elif phase == "discussion":
            model = task.discussion_model or task.model
        else:
            model = task.summary_model or task.model
        return ModelSelection(
            model=model,
            thinking_enabled="flash" not in model,
            reasoning_effort="high" if "pro" in model else "medium",
            route_reason=f"payload-model:{phase}",
        )

    def _has_actionable_blockers(self, evidence: list[CommandEvidence]) -> bool:
        return any(item.status in {"failed", "timeout", "unavailable"} for item in evidence[-4:])

    def _extract_promoted_notes(self, content: str) -> list[str]:
        core_section_notes: list[str] = []
        keyword_notes: list[str] = []
        fallback: list[str] = []
        in_core_section = False
        action_tokens = (
            "必要时",
            "如需",
            "疑似",
            "若确证",
            "若存在",
            "未知漏洞",
            "未建立利用上下文",
            "尚不能",
            "当前证据仅能说明",
            "只要补全",
            "即可立即",
            "下一步",
            "后续",
            "第一次溢出",
            "第二次溢出",
            "建议",
            "需进一步",
            "可按",
            "未证实",
            "未完成",
            "尚需",
            "需由",
            "需补充",
            "待补",
            "限制因素",
            "缺失工具影响",
            "完全没有执行",
            "无法给出",
            "无法形成",
            "未产生有效数据",
            "实际运行并观察",
            "需先",
            "必须",
            "需要",
            "才能",
            "缺失",
            "缺少",
            "无法",
            "推断",
            "潜在",
            "若证实",
            "未获得",
            "未捕获",
            "未验证",
            "未证明",
        )
        keyword_tokens = ("核心结论", "函数风险", "利用性判断", "格式化字符串", "溢出", "漏洞")
        heading_notes = {
            "已验证发现",
            "关键函数深度分析",
            "利用性判断",
            "值得提升为核心笔记的结论",
            "关键结论",
        }

        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            normalized_heading = line.lstrip("#").strip()
            if "值得提升为核心笔记的结论" in normalized_heading or normalized_heading == "关键结论":
                in_core_section = True
                continue
            if line.startswith("#") and re.match(r"^#+\s*[1-3]\.\s+", line):
                in_core_section = False

            note = self._parse_promoted_note_line(line)
            if note is None or any(token in note for token in action_tokens):
                continue
            if note.startswith(("若", "如果", "否则若", "如若")) or re.search(
                r"(?:^|[：:，,（(])(?:若|如果|否则若|如若)",
                note,
            ):
                continue
            if note.endswith("：") or note.startswith("`"):
                continue
            if note in heading_notes:
                continue

            if in_core_section:
                if note not in core_section_notes:
                    core_section_notes.append(note)
                continue

            if any(token in note for token in keyword_tokens):
                if note not in keyword_notes:
                    keyword_notes.append(note)
                continue

            if re.match(r"^\d+\.\s+", line):
                continue

            if note not in fallback:
                fallback.append(note)

        return (core_section_notes + keyword_notes + fallback)[:4]

    def _parse_promoted_note_line(self, line: str) -> str | None:
        if line.startswith("- "):
            return line[2:].strip()
        match = re.match(r"^\d+\.\s+(.*)$", line)
        if match:
            return match.group(1).strip()
        return None


class InProcessSubAgentRuntime:
    def __init__(self, settings: Settings, llm_backend: LLMBackend | None = None) -> None:
        self.settings = settings
        self.worker = SubAgentWorker(settings, llm_backend=llm_backend)

    async def run(
        self,
        payload: SubAgentPayload,
        event_sink: EventSink | None = None,
    ) -> SubAgentResult:
        return await self.worker.execute(payload, event_sink=event_sink)

    def clear_role_states(self, session_id: str) -> None:
        self.worker.clear_role_state(session_id)

    async def cleanup_session(self, session_id: str) -> None:
        self.clear_role_states(session_id)
        shutil.rmtree(self.settings.runtime_dir / session_id, ignore_errors=True)


class DockerSubAgentRuntime:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def run(
        self,
        payload: SubAgentPayload,
        event_sink: EventSink | None = None,
    ) -> SubAgentResult:
        runtime_dir = self.settings.runtime_dir / payload.session_id / payload.task.id
        coordination_dir = self.settings.runtime_dir / payload.session_id / "coordination"
        runtime_dir.mkdir(parents=True, exist_ok=True)
        coordination_dir.mkdir(parents=True, exist_ok=True)

        container_payload = payload.model_copy(deep=True)
        container_payload.target_path = self._prepare_container_target(payload.target_path, runtime_dir)
        container_payload.task.target_path = container_payload.target_path
        container_payload.event_stream_path = "/runtime/events.ndjson"
        container_payload.coordination_dir = "/coordination"
        cidfile_path = runtime_dir / "container.cid"
        staged_ida_user_dir = self._prepare_ida_user_dir(runtime_dir)
        container_ida_path = self._container_ida_headless_path()
        container_ida_install_dir = self._container_ida_install_dir()

        payload_path = runtime_dir / "payload.json"
        result_path = runtime_dir / "result.json"
        event_path = runtime_dir / "events.ndjson"
        payload_path.write_text(
            json.dumps(container_payload.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        command = [
            "docker",
            "run",
            "--rm",
            "--network",
            self._network_mode(),
            "--cidfile",
            str(cidfile_path),
            "-e",
            f"LLM_API_KEY={self.settings.llm_api_key or ''}",
            "-e",
            f"LLM_BASE_URL={self.settings.llm_base_url}",
            "-e",
            f"DEEPSEEK_API_KEY={self.settings.llm_api_key or ''}",
            "-e",
            f"DEEPSEEK_BASE_URL={self.settings.llm_base_url}",
            "-e",
            f"LOOP_THRESHOLD={self.settings.loop_threshold}",
            "-e",
            f"NOTE_RECALL_THRESHOLD={self.settings.note_recall_threshold}",
            "-e",
            f"ROUND_RESET_THRESHOLD={self.settings.round_reset_threshold}",
            "-e",
            f"AGENT_COORDINATION_TIMEOUT_SECONDS={self.settings.agent_coordination_timeout_seconds}",
            "-e",
            f"TOOL_TIMEOUT_SECONDS={self.settings.tool_timeout_seconds}",
            "-e",
            f"TOOL_OUTPUT_LIMIT={self.settings.tool_output_limit}",
            "-e",
            f"DISABLED_TOOL_IDS={self.settings.disabled_tool_ids_raw}",
            "-e",
            f"IDA_HEADLESS_PATH={container_ida_path}",
            "-e",
            f"TVHEADLESS=1",
            "-e",
            f"ROOTFS_ELF_TOOL_DIR={self.settings.container_rootfs_elf_tool_dir}",
            "-v",
            f"{self.settings.host_workspace_dir}:/workspace",
            "-v",
            f"{runtime_dir}:/runtime",
            "-v",
            f"{coordination_dir}:/coordination",
        ]

        if self.settings.host_ida_install_dir is not None:
            command.extend(
                [
                    "-v",
                    f"{self.settings.host_ida_install_dir}:{container_ida_install_dir}:ro",
                ]
            )
        if staged_ida_user_dir is not None:
            command.extend(
                [
                    "-v",
                    f"{staged_ida_user_dir}:{self.settings.container_ida_user_dir}",
                ]
            )
        if self.settings.rootfs_elf_tool_dir is not None and self.settings.rootfs_elf_tool_dir.exists():
            command.extend(
                [
                    "-v",
                    f"{self.settings.rootfs_elf_tool_dir}:{self.settings.container_rootfs_elf_tool_dir}:ro",
                ]
            )

        command.extend(
            [
                self.settings.subagent_docker_image,
            "/runtime/payload.json",
            "/runtime/result.json",
            ]
        )

        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        tail_task = None
        if event_sink is not None:
            tail_task = asyncio.create_task(self._tail_event_stream(event_path, process, event_sink))
        try:
            stdout, stderr = await process.communicate()
        except asyncio.CancelledError:
            await self._terminate_process(process)
            await self._stop_container_by_cidfile(cidfile_path)
            if tail_task is not None:
                tail_task.cancel()
                await asyncio.gather(tail_task, return_exceptions=True)
            raise
        if tail_task is not None:
            await tail_task
        if process.returncode != 0:
            raise RuntimeError(
                "Docker sub-agent failed: "
                + stdout.decode("utf-8", errors="replace")
                + stderr.decode("utf-8", errors="replace")
            )

        if not result_path.exists():
            raise RuntimeError("Docker sub-agent did not produce result.json")

        data = json.loads(result_path.read_text(encoding="utf-8"))
        result = SubAgentResult.model_validate(data)
        if cidfile_path.exists():
            result.container_id = cidfile_path.read_text(encoding="utf-8").strip() or result.container_id
        return result

    def _network_mode(self) -> str:
        configured = self.settings.subagent_docker_network_mode.strip().lower()
        if configured and configured != "auto":
            return configured
        return "bridge" if self.settings.llm_api_key else "none"

    def _prepare_container_target(self, host_path: str, runtime_dir: Path) -> str:
        host = Path(host_path).resolve()
        workspace = self.settings.host_workspace_dir.resolve()
        try:
            relative = host.relative_to(workspace)
        except ValueError:
            relative = None

        if relative is not None:
            ensure_target_executable(host)
            return str(Path("/workspace") / relative)
        if not host.exists():
            raise RuntimeError(f"Target path does not exist: {host_path}")
        if not host.is_file():
            raise RuntimeError(f"Docker sub-agent currently expects a file target, got: {host_path}")

        staged_dir = runtime_dir / "inputs"
        staged_dir.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha1(str(host).encode("utf-8")).hexdigest()[:12]
        staged_name = f"{host.stem}-{digest}{host.suffix}"
        staged_path = staged_dir / staged_name
        shutil.copy2(host, staged_path)
        ensure_target_executable(staged_path)
        return str(Path("/runtime") / "inputs" / staged_name)

    def _prepare_ida_user_dir(self, runtime_dir: Path) -> Path | None:
        source = self.settings.host_ida_user_dir
        if source is None or not source.exists():
            return None
        staged_dir = runtime_dir / "ida-user"
        shutil.copytree(
            source,
            staged_dir,
            dirs_exist_ok=True,
            ignore_dangling_symlinks=True,
        )
        return staged_dir

    def _container_ida_headless_path(self) -> str:
        host_install = self.settings.host_ida_install_dir
        host_executable = self.settings.ida_headless_path
        if host_install is not None and host_executable is not None:
            try:
                host_executable.resolve().relative_to(host_install.resolve())
            except ValueError:
                pass
            else:
                return str(host_executable.resolve())
        return self.settings.container_ida_path

    def _container_ida_install_dir(self) -> str:
        host_install = self.settings.host_ida_install_dir
        host_executable = self.settings.ida_headless_path
        if host_install is not None and host_executable is not None:
            try:
                host_executable.resolve().relative_to(host_install.resolve())
            except ValueError:
                pass
            else:
                return str(host_install.resolve())
        return str(Path(self.settings.container_ida_path).parent)

    async def _tail_event_stream(
        self,
        event_path: Path,
        process: asyncio.subprocess.Process,
        event_sink: EventSink,
    ) -> None:
        position = 0
        buffer = ""
        while True:
            if event_path.exists():
                chunk, position = await asyncio.to_thread(self._read_delta, event_path, position)
                if chunk:
                    buffer += chunk
                    lines = buffer.splitlines(keepends=False)
                    if chunk and not chunk.endswith("\n"):
                        buffer = lines.pop() if lines else buffer
                    else:
                        buffer = ""
                    for line in lines:
                        if not line.strip():
                            continue
                        await event_sink(AuditEvent.model_validate(json.loads(line)))

            if process.returncode is not None:
                if buffer.strip():
                    await event_sink(AuditEvent.model_validate(json.loads(buffer)))
                break
            await asyncio.sleep(0.15)

    def _read_delta(self, path: Path, position: int) -> tuple[str, int]:
        with path.open("r", encoding="utf-8") as handle:
            handle.seek(position)
            chunk = handle.read()
            return chunk, handle.tell()

    def clear_role_states(self, session_id: str) -> None:
        # Docker runtime does not persist in-process conversation state; each
        # subagent runs in a fresh container. File-based role-state persistence
        # is deferred to Phase D. No-op here so the Manager can call uniformly.
        return None

    async def cleanup_session(self, session_id: str) -> None:
        self.clear_role_states(session_id)
        session_dir = self.settings.runtime_dir / session_id
        for cidfile_path in session_dir.glob("**/container.cid"):
            await self._stop_container_by_cidfile(cidfile_path)
        shutil.rmtree(session_dir, ignore_errors=True)

    async def _stop_container_by_cidfile(self, cidfile_path: Path) -> None:
        if not cidfile_path.exists():
            return
        container_id = cidfile_path.read_text(encoding="utf-8").strip()
        if not container_id:
            return
        process = await asyncio.create_subprocess_exec(
            "docker",
            "rm",
            "-f",
            container_id,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await process.communicate()

    async def _terminate_process(self, process: asyncio.subprocess.Process) -> None:
        if process.returncode is not None:
            return
        process.kill()
        try:
            await process.communicate()
        except ProcessLookupError:
            return
