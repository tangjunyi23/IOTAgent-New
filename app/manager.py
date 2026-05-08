from __future__ import annotations

import asyncio
import hashlib
import json
import re
import shlex
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from fastapi import UploadFile

from app.config import Settings, ensure_directories, parse_tool_id_csv
from app.llm import LLMBackend, MissingDeepSeekLLMBackend, create_llm_backend, probe_deepseek_connection
from app.model_router import ModelRouter, ModelSelection
from app.models import (
    ArtifactRecord,
    AuditEvent,
    AuditReportExport,
    AuditRequest,
    AuditSession,
    DeepSeekCheckResult,
    DeepSeekSettingsView,
    DifficultyHint,
    EventKind,
    ExportedSubAgentReport,
    KnowledgeEntry,
    ManagerPlanOutline,
    ManagerPlanPhase,
    ManagerPlanRole,
    NoteEntry,
    ReportExportFormat,
    SessionStatus,
    SystemSettingsView,
    SharedMemoryEntry,
    SubAgentPayload,
    SubAgentStatus,
    SubAgentTask,
    SystemSettingsUpdate,
    TokenUsageSnapshot,
    ToolCapability,
    utcnow,
)
from app.pwn_skill import PwnSkillPack
from app.realtime import AuditEventBroker
from app.repository import JsonRepository
from app.subagent import DockerSubAgentRuntime, InProcessSubAgentRuntime
from app.target_utils import ensure_target_executable


@dataclass
class FunctionReportEntry:
    name: str
    address: str | None = None
    roles: set[str] = field(default_factory=set)
    tools: set[str] = field(default_factory=set)
    issue_lines: list[str] = field(default_factory=list)
    fact_lines: list[str] = field(default_factory=list)
    caller_lines: list[str] = field(default_factory=list)
    caller_refs: list[tuple[str, str | None]] = field(default_factory=list)
    dangerous_call_refs: list[tuple[str, str | None]] = field(default_factory=list)
    score: int = 0


@dataclass
class PlannedSubAgent:
    role: str
    objective: str
    coordination_focus: list[str] = field(default_factory=list)
    collaboration_targets: list[str] = field(default_factory=list)
    expected_evidence: list[str] = field(default_factory=list)
    stage_goal: str | None = None
    expected_evidence_is_default: bool = False
    stage_goal_is_default: bool = False
    priority: int = 100


class LLMNotReadyError(RuntimeError):
    """Raised when the platform cannot start a new audit because the LLM backend is unavailable."""


class ManagerAgentService:
    HOT_EDITABLE_SETTINGS: tuple[str, ...] = (
        "deepseek_base_url",
        "manager_regular_model",
        "manager_hard_model",
        "upload_dir",
        "audit_dir",
        "artifact_meta_dir",
        "runtime_dir",
        "skill_data_dir",
        "knowledge_deleted_path",
        "enable_docker_runtime",
        "subagent_docker_image",
        "subagent_docker_network_mode",
        "host_workspace_dir",
        "max_parallel_subagents",
        "loop_threshold",
        "note_recall_threshold",
        "round_reset_threshold",
        "agent_discussion_max_rounds",
        "agent_coordination_timeout_seconds",
        "llm_timeout_seconds",
        "tool_output_limit",
        "tool_timeout_seconds",
        "ida_headless_path",
        "host_ida_install_dir",
        "host_ida_user_dir",
        "rootfs_elf_tool_dir",
    )
    INCOMPLETE_TOKENS: tuple[str, ...] = (
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
        "无法确认",
        "无法判断",
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
        "未满足",
        "未在本轮",
    )

    def __init__(
        self,
        settings: Settings,
        repository: JsonRepository,
        broker: AuditEventBroker,
    ) -> None:
        self.settings = settings
        self.repository = repository
        self.broker = broker
        self.router = ModelRouter(settings)
        self.llm_backend: LLMBackend = create_llm_backend(settings)
        self.pwn_skill = PwnSkillPack(settings)
        self.toolbox = self._create_toolbox()
        self.runtime = self._create_runtime()
        self.running_sessions: dict[str, asyncio.Task] = {}
        self.session_locks: dict[str, asyncio.Lock] = {}

    def _create_toolbox(self):
        from app.toolbox import BinaryToolbox

        return BinaryToolbox(self.settings)

    def _create_runtime(self):
        if self.settings.enable_docker_runtime:
            return DockerSubAgentRuntime(self.settings)
        return InProcessSubAgentRuntime(self.settings, llm_backend=self.llm_backend)

    def _refresh_tool_runtime(self) -> None:
        self.toolbox = self._create_toolbox()
        self.runtime = self._create_runtime()

    def _llm_runtime_state(self) -> dict[str, object]:
        configured = bool((self.settings.deepseek_api_key or "").strip())
        status = "ready"
        error: str | None = None
        if isinstance(self.llm_backend, MissingDeepSeekLLMBackend):
            status = "missing_api_key"
            error = self.llm_backend.message
        elif not configured:
            status = "missing_api_key"
            error = "DeepSeek API key is not configured."
        return {
            "llm_backend": type(self.llm_backend).__name__,
            "llm_provider": "deepseek",
            "llm_status": status,
            "llm_configured": configured,
            "llm_error": error,
        }

    def ensure_llm_ready(self) -> None:
        runtime_state = self._llm_runtime_state()
        if runtime_state["llm_status"] == "ready":
            return
        raise LLMNotReadyError(str(runtime_state.get("llm_error") or "DeepSeek backend is not ready."))

    async def store_artifact(self, upload: UploadFile) -> ArtifactRecord:
        artifact_id = hashlib.sha1(f"{upload.filename}:{asyncio.get_running_loop().time()}".encode()).hexdigest()
        target_dir = self.settings.upload_dir / artifact_id
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / (upload.filename or "sample.bin")

        digest = hashlib.sha256()
        size_bytes = 0
        with target_path.open("wb") as handle:
            while chunk := await upload.read(1024 * 1024):
                handle.write(chunk)
                size_bytes += len(chunk)
                digest.update(chunk)
        ensure_target_executable(target_path)

        artifact = ArtifactRecord(
            id=artifact_id,
            filename=upload.filename or "sample.bin",
            stored_path=str(target_path),
            sha256=digest.hexdigest(),
            size_bytes=size_bytes,
        )
        self.repository.save_artifact(artifact)
        return artifact

    async def create_session(self, request: AuditRequest) -> AuditSession:
        self.ensure_llm_ready()
        resolved_path = await self._resolve_target_path(request)
        normalized_request = request.model_copy(deep=True)
        normalized_request.target_path = resolved_path
        core_notes = self._build_core_notes(normalized_request, resolved_path)
        session = AuditSession(
            request=normalized_request,
            core_notes=core_notes,
            shared_memory=self._build_initial_shared_memory(normalized_request, resolved_path),
            events=[
                AuditEvent(
                    kind=EventKind.SESSION_CREATED,
                    message="Audit session created",
                    payload={"target_path": resolved_path},
                )
            ],
        )
        self.repository.save_session(session)
        await self.broker.publish_event(session.id, session.events[-1])
        await self.broker.publish_snapshot(session)
        task = asyncio.create_task(self._run_session(session.id))
        self.running_sessions[session.id] = task
        return session

    def get_session(self, session_id: str) -> AuditSession:
        session = self.repository.load_session(session_id)
        return self._refresh_session_report(session)

    def list_sessions(self, limit: int = 20, *, compact: bool = False) -> list[AuditSession]:
        sessions = [self._refresh_session_report(item) for item in self.repository.list_sessions(limit=limit)]
        if not compact:
            return sessions
        return [self._compact_session_for_listing(item) for item in sessions]

    async def delete_session(self, session_id: str) -> None:
        try:
            session = self.repository.load_session(session_id)
        except FileNotFoundError:
            session = None
        running_task = self.running_sessions.get(session_id)
        if running_task is not None:
            running_task.cancel()
            await asyncio.gather(running_task, return_exceptions=True)

        await self.runtime.cleanup_session(session_id)
        self.repository.delete_session(session_id)
        self.session_locks.pop(session_id, None)
        if session is None:
            return
        self._prune_hidden_knowledge_entries_for_session(session)

        artifact_id = session.request.artifact_id
        if artifact_id and not self._artifact_referenced_elsewhere(artifact_id, excluding_session_id=session_id):
            self._delete_artifact_bundle(artifact_id)

    def list_knowledge_entries(self) -> list[KnowledgeEntry]:
        return self._build_knowledge_entries(include_hidden=False)

    def delete_knowledge_entry(self, entry_id: str) -> None:
        all_entries = self._build_knowledge_entries(include_hidden=True)
        if entry_id not in {entry.id for entry in all_entries}:
            raise FileNotFoundError(entry_id)
        hidden_ids = self.repository.load_hidden_knowledge_entry_ids()
        hidden_ids.add(entry_id)
        self.repository.save_hidden_knowledge_entry_ids(hidden_ids)

    def read_progress_document(self) -> str:
        return self.settings.progress_log_path.read_text(encoding="utf-8")

    def list_tool_capabilities(self) -> list[ToolCapability]:
        return self.toolbox.list_capabilities()

    def update_tool_enabled(self, tool_id: str, enabled: bool) -> ToolCapability:
        if tool_id not in self.toolbox.TOOL_DESCRIPTORS:
            raise FileNotFoundError(tool_id)
        disabled_ids = parse_tool_id_csv(self.settings.disabled_tool_ids_raw)
        if enabled:
            disabled_ids.discard(tool_id)
        else:
            disabled_ids.add(tool_id)
        rendered = ",".join(sorted(disabled_ids)) or None
        self.settings.disabled_tool_ids_raw = rendered or ""
        self._persist_env_value("DISABLED_TOOL_IDS", rendered)
        self._refresh_tool_runtime()
        return next(item for item in self.list_tool_capabilities() if item.tool_id == tool_id)

    def runtime_profile(self) -> dict[str, object]:
        return {
            **self._llm_runtime_state(),
            "regular_model": self.settings.manager_regular_model,
            "hard_model": self.settings.manager_hard_model,
            "docker_runtime": self.settings.enable_docker_runtime,
            "max_parallel_subagents": self.settings.max_parallel_subagents,
            "manager_round_policy": "result_driven",
            "manager_model_policy": "auto-by-round-complexity",
            "subagent_model_policy": "auto-by-phase",
            "token_tracking": "live-per-call",
            "disabled_tool_ids": sorted(parse_tool_id_csv(self.settings.disabled_tool_ids_raw)),
        }

    def deepseek_settings_view(self) -> DeepSeekSettingsView:
        configured = bool((self.settings.deepseek_api_key or "").strip())
        return DeepSeekSettingsView(
            configured=configured,
            key_preview=self._mask_api_key(self.settings.deepseek_api_key),
            base_url=self.settings.deepseek_base_url,
            status="ready" if configured else "missing_api_key",
        )

    def system_settings_view(self) -> SystemSettingsView:
        deepseek = self.deepseek_settings_view()
        return SystemSettingsView(
            deepseek_configured=deepseek.configured,
            deepseek_key_preview=deepseek.key_preview,
            deepseek_status=deepseek.status,
            deepseek_base_url=self.settings.deepseek_base_url,
            manager_regular_model=self.settings.manager_regular_model,
            manager_hard_model=self.settings.manager_hard_model,
            upload_dir=str(self.settings.upload_dir),
            audit_dir=str(self.settings.audit_dir),
            artifact_meta_dir=str(self.settings.artifact_meta_dir),
            runtime_dir=str(self.settings.runtime_dir),
            skill_data_dir=str(self.settings.skill_data_dir),
            knowledge_deleted_path=str(self.settings.knowledge_deleted_path),
            enable_docker_runtime=self.settings.enable_docker_runtime,
            subagent_docker_image=self.settings.subagent_docker_image,
            subagent_docker_network_mode=self.settings.subagent_docker_network_mode,
            host_workspace_dir=str(self.settings.host_workspace_dir),
            max_parallel_subagents=self.settings.max_parallel_subagents,
            loop_threshold=self.settings.loop_threshold,
            note_recall_threshold=self.settings.note_recall_threshold,
            round_reset_threshold=self.settings.round_reset_threshold,
            agent_discussion_max_rounds=self.settings.agent_discussion_max_rounds,
            agent_coordination_timeout_seconds=self.settings.agent_coordination_timeout_seconds,
            llm_timeout_seconds=self.settings.llm_timeout_seconds,
            tool_output_limit=self.settings.tool_output_limit,
            tool_timeout_seconds=self.settings.tool_timeout_seconds,
            ida_headless_path=str(self.settings.ida_headless_path) if self.settings.ida_headless_path else None,
            host_ida_install_dir=str(self.settings.host_ida_install_dir) if self.settings.host_ida_install_dir else None,
            host_ida_user_dir=str(self.settings.host_ida_user_dir) if self.settings.host_ida_user_dir else None,
            rootfs_elf_tool_dir=str(self.settings.rootfs_elf_tool_dir) if self.settings.rootfs_elf_tool_dir else None,
        )

    def update_deepseek_api_key(self, api_key: str | None) -> DeepSeekSettingsView:
        normalized = (api_key or "").strip() or None
        self._apply_settings_patch({"deepseek_api_key": normalized})
        return self.deepseek_settings_view()

    def update_system_settings(self, payload: SystemSettingsUpdate) -> SystemSettingsView:
        updates = {
            key: value
            for key, value in payload.model_dump(exclude_unset=True).items()
            if key in self.HOT_EDITABLE_SETTINGS
        }
        if not updates:
            return self.system_settings_view()
        self._apply_settings_patch(updates)
        return self.system_settings_view()

    async def check_deepseek_api(self, api_key: str | None = None) -> DeepSeekCheckResult:
        normalized = (api_key or "").strip() or None
        if not normalized and not (self.settings.deepseek_api_key or "").strip():
            return DeepSeekCheckResult(
                available=False,
                model=self.settings.manager_regular_model,
                status="missing_api_key",
                error="DeepSeek API key is not configured.",
            )
        try:
            await probe_deepseek_connection(self.settings, api_key=normalized)
        except Exception as exc:
            return DeepSeekCheckResult(
                available=False,
                model=self.settings.manager_regular_model,
                status="error",
                error=str(exc),
            )
        return DeepSeekCheckResult(
            available=True,
            model=self.settings.manager_regular_model,
            status="ready",
        )

    def build_report_export(self, session_id: str) -> AuditReportExport:
        session = self._refresh_session_report(self.repository.load_session(session_id))
        return AuditReportExport(
            session_id=session.id,
            title=self._report_title(session),
            status=session.status,
            target_path=session.request.target_path,
            objective=session.request.objective,
            difficulty=session.request.difficulty,
            tags=session.request.tags,
            core_notes=[note.content for note in session.core_notes],
            report_markdown=self._report_markdown(session),
            subagents=[
                ExportedSubAgentReport(
                    task_id=task.id,
                    role=task.role,
                    model=task.model,
                    status=task.status,
                    token_usage=task.token_usage,
                    summary=task.output_summary,
                    plan_summary=task.plan_summary,
                    promoted_notes=task.promoted_notes,
                    evidence=task.evidence,
                    interventions=task.interventions,
                    error=task.error,
                )
                for task in session.subagents
            ],
        )

    def report_filename(self, session_id: str, export_format: ReportExportFormat) -> str:
        session = self.repository.load_session(session_id)
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", self._report_title(session)).strip("-").lower()
        prefix = slug or "audit-report"
        suffix = "md" if export_format == ReportExportFormat.MARKDOWN else "json"
        return f"{prefix}-{session.id[:8]}.{suffix}"

    async def _resolve_target_path(self, request: AuditRequest) -> str:
        if request.artifact_id:
            artifact = self.repository.load_artifact(request.artifact_id)
            return artifact.stored_path
        assert request.target_path is not None
        target = Path(request.target_path)
        if not target.is_absolute():
            target = (self.settings.host_workspace_dir / target).resolve()
        return str(target)

    def _build_core_notes(self, request: AuditRequest, target_path: str) -> list[NoteEntry]:
        notes = [
            NoteEntry(content=f"任务标题: {request.title}", source="manager", is_core=True),
            NoteEntry(content=f"审计目标: {request.objective}", source="manager", is_core=True),
            NoteEntry(content=f"目标路径: {target_path}", source="manager", is_core=True),
            NoteEntry(content=f"难度标签: {request.difficulty}", source="manager", is_core=True),
        ]
        if self.pwn_skill.available:
            notes.append(
                NoteEntry(
                    content=(
                        "已启用 ctf-pwn skill：本轮应优先产出可复现的动态取证与已验证 POC，"
                        "并保持结论以运行时证据和函数级分析为准。"
                        "最终结论必须显式回答当前 exploit stage 是否已推进到 RCE / getshell。"
                    ),
                    source="skill:ctf-pwn",
                    is_core=True,
                )
            )
        notes.extend(
            NoteEntry(content=item, source="analyst", is_core=True)
            for item in request.analyst_notes
        )
        return notes

    def _build_initial_shared_memory(self, request: AuditRequest, target_path: str) -> list[SharedMemoryEntry]:
        entries = [
            SharedMemoryEntry(
                content=f"固定信息：目标路径为 {target_path}。",
                source="manager",
                category="fixed",
                priority=120,
            ),
            SharedMemoryEntry(
                content=f"固定信息：本次审计目标是 {request.objective}",
                source="manager",
                category="fixed",
                priority=118,
            ),
            SharedMemoryEntry(
                content=f"固定信息：难度标签为 {request.difficulty}。",
                source="manager",
                category="fixed",
                priority=112,
            ),
        ]
        for item in request.analyst_notes[:3]:
            entries.append(
                SharedMemoryEntry(
                    content=f"分析师固定说明：{item}",
                    source="analyst",
                    category="fixed",
                    priority=108,
                )
            )
        if self.pwn_skill.available:
            entries.append(
                SharedMemoryEntry(
                    content="固定约束：优先复用动态取证和函数级证据，最终必须明确当前 exploit stage 是否达到 RCE / getshell。",
                    source="skill:ctf-pwn",
                    category="fixed",
                    priority=116,
                )
            )
        return entries

    def _build_manager_round_core_notes(self, session: AuditSession, round_index: int) -> list[str]:
        notes = [note.content for note in session.core_notes[:4]]
        notes.extend(
            f"共享记忆: {entry.content}"
            for entry in self._select_shared_memory_for_manager(session, limit=6)
        )
        if round_index <= 1:
            notes.append("规划约束：首轮优先选择最少但互补的角色组合，不要预留重复基础工具。")
            return self._dedupe_text_items(notes, limit=14)

        notes.append(f"当前进入 Manager 第 {round_index} 轮规划，必须基于共享记忆与前序已完成证据继续推进。")
        notes.append("规划约束：下一轮只能补未覆盖的证据缺口，优先复用上一轮已完成工具结果，禁止重复基础工具链。")
        notes.extend(self._build_prior_role_digests(session, before_round=round_index, limit=4))

        manager_highlights = self._collect_manager_highlights(session)
        for item in manager_highlights[:4]:
            notes.append(f"已完成取证结论: {item}")

        rce_sections = self._build_rce_assessment_section(session)
        for item in rce_sections[:3]:
            notes.append(item.lstrip("- ").strip())

        prior_round_tasks = [task for task in session.subagents if task.round_index < round_index]
        blocker_lines: list[str] = []
        for task in prior_round_tasks[-6:]:
            for evidence in task.evidence[-6:]:
                if evidence.status in {"failed", "timeout", "unavailable"}:
                    blocker_lines.append(
                        f"{task.role}[第{task.round_index}轮] {evidence.command_id}={evidence.status}"
                    )
        for item in blocker_lines[:3]:
            notes.append(f"当前阻塞: {item}")
        return self._dedupe_text_items(notes, limit=18)

    def _dedupe_text_items(self, items: list[str], *, limit: int) -> list[str]:
        cleaned: list[str] = []
        seen: set[str] = set()
        for item in items:
            text = re.sub(r"\s+", " ", str(item or "")).strip()
            if not text or text in seen:
                continue
            seen.add(text)
            cleaned.append(text)
            if len(cleaned) >= limit:
                break
        return cleaned

    def _select_shared_memory_for_manager(
        self,
        session: AuditSession,
        *,
        limit: int,
    ) -> list[SharedMemoryEntry]:
        ranked = sorted(
            session.shared_memory,
            key=lambda item: (
                item.priority,
                item.round_index or 0,
                item.created_at,
            ),
            reverse=True,
        )
        selected: list[SharedMemoryEntry] = []
        fixed_selected = 0
        for item in ranked:
            if item.category == "fixed":
                if fixed_selected >= 4:
                    continue
                fixed_selected += 1
            selected.append(item)
            if len(selected) >= limit:
                break
        return list(reversed(selected))

    def _build_prior_role_digests(
        self,
        session: AuditSession,
        *,
        before_round: int,
        limit: int,
    ) -> list[str]:
        latest_by_role: dict[str, SubAgentTask] = {}
        for task in session.subagents:
            if task.round_index >= before_round:
                continue
            latest_by_role[task.role] = task

        digests: list[str] = []
        for role, task in latest_by_role.items():
            completed_tools = [item.command_id for item in task.evidence if item.status == "completed"]
            if completed_tools:
                digests.append(
                    f"{role} 第{task.round_index}轮已完成工具: {', '.join(completed_tools[:6])}"
                )
            key_points = self._select_task_key_points(task, self._collect_manager_highlights(session), limit=2)
            if key_points:
                digests.append(
                    f"{role} 第{task.round_index}轮关键结论: {'；'.join(key_points[:2])}"
                )
            blockers = [
                f"{item.command_id}={item.status}"
                for item in task.evidence[-4:]
                if item.status in {"failed", "timeout", "unavailable"}
            ]
            if blockers:
                digests.append(
                    f"{role} 第{task.round_index}轮已知阻塞: {'；'.join(blockers[:2])}"
                )
        return self._dedupe_text_items(digests, limit=limit)

    def _promote_round_core_notes(self, session: AuditSession, round_index: int) -> None:
        existing = {note.content for note in session.core_notes}
        appended = 0
        for task in [item for item in session.subagents if item.round_index == round_index]:
            for point in self._select_task_key_points(task, self._collect_manager_highlights(session), limit=2):
                content = f"[第{round_index}轮/{task.role}] {point}"
                if content in existing:
                    continue
                session.core_notes.append(
                    NoteEntry(
                        content=content,
                        source=f"manager:round-{round_index}",
                        is_core=True,
                    )
                )
                existing.add(content)
                appended += 1
                if appended >= 4:
                    return

    def _append_shared_memory_entry(
        self,
        session: AuditSession,
        *,
        content: str,
        source: str,
        category: str,
        round_index: int | None = None,
        role: str | None = None,
        priority: int = 0,
    ) -> None:
        normalized = re.sub(r"\s+", " ", str(content or "")).strip()
        if not normalized:
            return
        if any(re.sub(r"\s+", " ", item.content).strip() == normalized for item in session.shared_memory):
            return
        session.shared_memory.append(
            SharedMemoryEntry(
                content=normalized,
                source=source,
                category=category,
                round_index=round_index,
                role=role,
                priority=priority,
            )
        )

    def _refresh_shared_memory_from_round(
        self,
        session: AuditSession,
        round_index: int,
        correction_summary: str,
    ) -> None:
        if correction_summary:
            self._append_shared_memory_entry(
                session,
                content=f"第{round_index}轮复盘：{correction_summary}",
                source="manager",
                category="round-summary",
                round_index=round_index,
                priority=96,
            )

        for task in [item for item in session.subagents if item.round_index == round_index]:
            key_points = self._select_task_key_points(task, self._collect_manager_highlights(session), limit=2)
            for point in key_points:
                self._append_shared_memory_entry(
                    session,
                    content=point,
                    source=f"task:{task.role}",
                    category="finding",
                    round_index=round_index,
                    role=task.role,
                    priority=self._shared_memory_priority(point),
                )
            blockers = [
                f"{task.role} 第{round_index}轮阻塞: {item.command_id}={item.status}"
                for item in task.evidence[-4:]
                if item.status in {"failed", "timeout", "unavailable"}
            ]
            for blocker in blockers[:2]:
                self._append_shared_memory_entry(
                    session,
                    content=blocker,
                    source=f"task:{task.role}",
                    category="blocker",
                    round_index=round_index,
                    role=task.role,
                    priority=84,
                )
        self._trim_shared_memory(session)

    def _shared_memory_priority(self, text: str) -> int:
        score = 60
        weights = (
            ("RCE", 40),
            ("getshell", 40),
            ("命令执行", 32),
            ("RIP", 28),
            ("控制流", 28),
            ("格式化字符串", 22),
            ("溢出", 18),
            ("信息泄露", 16),
            ("危险导入", 12),
            ("阻塞", 8),
        )
        for token, value in weights:
            if token in text:
                score += value
        return score

    def _trim_shared_memory(self, session: AuditSession) -> None:
        fixed = [item for item in session.shared_memory if item.category == "fixed"]
        dynamic = [item for item in session.shared_memory if item.category != "fixed"]
        dynamic = sorted(
            dynamic,
            key=lambda item: (
                item.priority,
                item.round_index or 0,
                item.created_at,
            ),
            reverse=True,
        )[:12]
        session.shared_memory = sorted(
            fixed[:6] + dynamic,
            key=lambda item: (
                item.round_index or 0,
                item.priority,
                item.created_at,
            ),
        )

    def _should_continue_manager_rounds(
        self,
        session: AuditSession,
        round_index: int,
    ) -> tuple[bool, str]:
        payloads = self._collect_rce_payloads(session)
        if any(item["stage_id"] in {"code-exec", "getshell"} for item in payloads):
            return False, ""

        latest_round_tasks = [task for task in session.subagents if task.round_index == round_index]
        has_completed = any(task.status == SubAgentStatus.COMPLETED for task in latest_round_tasks)
        if not has_completed:
            return False, ""

        manager_pending = [
            f"{task.role}({task.manager_step_completed}/{max(1, task.manager_step_total)})"
            for task in latest_round_tasks
            if task.status == SubAgentStatus.COMPLETED and not task.manager_completion_confirmed
        ]
        if manager_pending:
            return True, f"Manager 复核后仍有角色未完成计划检查点：{'；'.join(manager_pending[:2])}。"

        blockers = [
            f"{task.role}:{evidence.command_id}={evidence.status}"
            for task in latest_round_tasks
            for evidence in task.evidence[-6:]
            if evidence.status in {"failed", "timeout", "unavailable"}
        ]
        static_candidates = self._collect_static_rce_candidates(session)
        if payloads:
            ranked = sorted(payloads, key=lambda item: self._rce_stage_rank(item["stage_id"]), reverse=True)
            best = ranked[0]
            if best["stage_id"] not in {"code-exec", "getshell"}:
                reason = f"当前最高 exploit stage 为 {best['stage_label']}，尚未到 RCE / getshell。"
                if blockers:
                    reason += f" 同时仍有关键阻塞：{'；'.join(blockers[:2])}。"
                return True, reason
        if static_candidates:
            return True, "当前已锁定函数级危险原语，但缺少足以把结论推进到 RCE / getshell 的动态证据。"
        if blockers:
            return True, f"当前仍有关键工具阻塞：{'；'.join(blockers[:2])}，Manager 将改走下一轮证据路径。"
        return False, ""

    async def _run_session(self, session_id: str) -> None:
        session = self.repository.load_session(session_id)
        session.status = SessionStatus.RUNNING
        session.manager_round = 0
        started_event = AuditEvent(kind=EventKind.SESSION_STARTED, message="Manager agent started orchestration")
        session.events.append(started_event)
        self.repository.save_session(session)
        await self.broker.publish_event(session.id, started_event)
        await self.broker.publish_snapshot(session)

        semaphore = asyncio.Semaphore(self.settings.max_parallel_subagents)

        async def run_one(task: SubAgentTask):
            async with semaphore:
                return await self._run_subagent(session, task)

        try:
            round_index = 1
            while True:
                session = self.repository.load_session(session_id)
                session.manager_round = round_index
                planning_event = AuditEvent(
                    kind=EventKind.REASONING_ROUND,
                    message=f"Manager agent is building orchestration round {round_index}",
                    payload={"scope": "manager", "round_index": round_index},
                )
                session.events.append(planning_event)
                self.repository.save_session(session)
                await self.broker.publish_event(session.id, planning_event)
                await self.broker.publish_snapshot(session)

                manager_plan_summary, manager_plan, subagent_tasks = await self._plan_subagents(session, round_index=round_index)
                session = self.repository.load_session(session_id)
                session.manager_round = round_index
                session.manager_plan_summary = manager_plan_summary
                session.manager_plan = manager_plan
                session.manager_plan_history.append(manager_plan)
                session.subagents.extend(subagent_tasks)
                plan_complete_event = AuditEvent(
                    kind=EventKind.REASONING_ROUND,
                    message=f"Manager agent completed orchestration round {round_index}",
                    payload={
                        "scope": "manager",
                        "round_index": round_index,
                        "roles": [task.role for task in subagent_tasks],
                        "manager_plan_summary": manager_plan_summary,
                    },
                )
                session.events.append(plan_complete_event)
                self.repository.save_session(session)
                await self.broker.publish_event(session.id, plan_complete_event)
                await self.broker.publish_snapshot(session)

                session = self.repository.load_session(session_id)
                round_tasks = [task for task in session.subagents if task.round_index == round_index]
                if not round_tasks:
                    break
                results = await asyncio.gather(*(run_one(task) for task in round_tasks))
                updated_session = self.repository.load_session(session_id)
                for result in results:
                    for task in updated_session.subagents:
                        if task.id != result.task_id:
                            continue
                        sanitized_summary = self._sanitize_subagent_summary(result.summary)
                        task.status = result.status
                        task.plan_summary = result.plan_summary
                        task.output_summary = sanitized_summary
                        task.token_usage = result.token_usage
                        task.evidence = result.evidence
                        task.interventions = result.interventions
                        task.promoted_notes = result.promoted_notes
                        task.events = result.events
                        task.container_id = result.container_id
                        task.finished_at = utcnow()
                        task.error = result.error
                        break
                correction_summary, approved_roles, pending_roles = self._apply_manager_round_review(
                    updated_session,
                    round_index,
                )
                self._promote_round_core_notes(updated_session, round_index)
                self._refresh_shared_memory_from_round(updated_session, round_index, correction_summary)
                self._recompute_session_token_usage(updated_session)
                if correction_summary:
                    correction_event = AuditEvent(
                        kind=EventKind.REASONING_ROUND,
                        message=f"Manager agent reviewed round {round_index} progress",
                        payload={
                            "scope": "manager",
                            "round_index": round_index,
                            "correction_summary": correction_summary,
                            "approved_roles": approved_roles,
                            "pending_roles": pending_roles,
                        },
                    )
                    updated_session.events.append(correction_event)
                self.repository.save_session(updated_session)
                await self.broker.publish_snapshot(updated_session)
                if correction_summary:
                    await self.broker.publish_event(updated_session.id, correction_event)

                continue_round, continue_reason = self._should_continue_manager_rounds(updated_session, round_index)
                if continue_round:
                    replan_event = AuditEvent(
                        kind=EventKind.REASONING_ROUND,
                        message=f"Manager agent is replanning for round {round_index + 1}",
                        payload={
                            "scope": "manager",
                            "round_index": round_index,
                            "next_round_index": round_index + 1,
                            "reason": continue_reason,
                        },
                    )
                    updated_session.events.append(replan_event)
                    self.repository.save_session(updated_session)
                    await self.broker.publish_event(updated_session.id, replan_event)
                    await self.broker.publish_snapshot(updated_session)
                    round_index += 1
                    continue
                break

            updated_session = self.repository.load_session(session_id)
            completed = sum(1 for task in updated_session.subagents if task.status == SubAgentStatus.COMPLETED)
            updated_session.status = SessionStatus.COMPLETED if completed > 0 else SessionStatus.FAILED
            updated_session.final_report = self._compose_final_report(updated_session)
            completion_event = AuditEvent(
                kind=(
                    EventKind.SESSION_COMPLETED
                    if updated_session.status == SessionStatus.COMPLETED
                    else EventKind.SESSION_FAILED
                ),
                message=f"Session finished with {completed}/{len(updated_session.subagents)} completed sub-agents",
            )
            updated_session.events.append(completion_event)
            self.repository.save_session(updated_session)
            await self.broker.publish_event(updated_session.id, completion_event)
            await self.broker.publish_snapshot(updated_session)
            self._cleanup_finished_uploaded_artifact(updated_session)
        except asyncio.CancelledError:
            return
        except Exception as exc:
            try:
                failed_session = self.repository.load_session(session_id)
            except FileNotFoundError:
                return
            failed_session.status = SessionStatus.FAILED
            failure_event = AuditEvent(kind=EventKind.SESSION_FAILED, message=f"Session failed: {exc}")
            failed_session.events.append(failure_event)
            self.repository.save_session(failed_session)
            await self.broker.publish_event(failed_session.id, failure_event)
            await self.broker.publish_snapshot(failed_session)
            self._cleanup_finished_uploaded_artifact(failed_session)
        finally:
            self.running_sessions.pop(session_id, None)

    async def _run_subagent(self, session: AuditSession, task: SubAgentTask):
        current_session = self.repository.load_session(session.id)
        seed_evidence = self._build_reusable_evidence(current_session, task)
        reused_tool_ids = list(dict.fromkeys(item.command_id for item in seed_evidence if item.command_id))
        shared_memory = self._select_shared_memory_for_task(current_session, task, limit=8)
        core_notes = self._build_subagent_core_notes(current_session)
        task.reused_tool_ids = list(reused_tool_ids)
        async with self._session_lock(session.id):
            current_session = self.repository.load_session(session.id)
            for item in current_session.subagents:
                if item.id == task.id:
                    item.status = SubAgentStatus.RUNNING
                    item.started_at = item.started_at or utcnow()
                    item.reused_tool_ids = list(reused_tool_ids)
                    item.events.append(
                        AuditEvent(
                            kind=EventKind.SUBAGENT_STARTED,
                            message=f"Sub-agent {item.role} started",
                            agent_id=item.id,
                        )
                    )
            self.repository.save_session(current_session)
        await self.broker.publish_snapshot(current_session)
        await self.broker.publish_event(
            session.id,
            AuditEvent(
                kind=EventKind.SUBAGENT_STARTED,
                message=f"Sub-agent {task.role} started",
                agent_id=task.id,
            ),
            task_id=task.id,
        )

        round_peers = [
            item
            for item in current_session.subagents
            if item.id != task.id and item.round_index == task.round_index
        ]

        payload = SubAgentPayload(
            session_id=session.id,
            session_title=session.request.title,
            task=task,
            core_notes=core_notes,
            shared_memory=shared_memory,
            seed_evidence=seed_evidence,
            objective=session.request.objective,
            target_path=session.request.target_path or task.target_path,
            manager_plan_summary=current_session.manager_plan_summary,
            coordination_dir=str(self.settings.runtime_dir / session.id / f"round-{task.round_index}" / "coordination"),
            peer_count=len(round_peers),
            peer_roles=[item.role for item in round_peers],
        )
        result = await self.runtime.run(
            payload,
            event_sink=lambda event: self._record_subagent_event(session.id, task.id, event),
        )
        await self._persist_subagent_result(session.id, result)
        return result

    async def _plan_subagents(
        self,
        session: AuditSession,
        *,
        round_index: int = 1,
    ) -> tuple[str, ManagerPlanOutline, list[SubAgentTask]]:
        request = session.request
        selection = self._manager_selection(session, round_index=round_index)
        plan_reply = await self.llm_backend.plan_session(
            request=request,
            core_notes=self._build_manager_round_core_notes(session, round_index),
            available_tools=self.list_tool_capabilities(),
            selection=selection,
        )
        await self._record_manager_llm_usage(
            session.id,
            reply=plan_reply,
            selection=selection,
            stage="manager-plan",
            round_index=round_index,
        )
        plan_payload = self._parse_manager_plan(plan_reply.content)
        planned_subagents = self._coerce_planned_subagents(request, plan_payload)
        plan_outline = self._build_manager_plan_outline(plan_reply.content, plan_payload, planned_subagents)
        plan_summary = self._render_manager_plan_summary(plan_outline)
        tasks: list[SubAgentTask] = []
        for item in planned_subagents:
            has_history = any(
                task.role == item.role and task.round_index < round_index
                for task in session.subagents
            )
            plan_model = self.router.select_for_subagent_phase(
                request,
                item.role,
                phase="plan",
                round_index=round_index,
                has_history=has_history,
                objective=item.objective,
            )
            discussion_model = self.router.select_for_subagent_phase(
                request,
                item.role,
                phase="discussion",
                round_index=round_index,
                has_history=has_history,
                objective=item.objective,
            )
            summary_model = self.router.select_for_subagent_phase(
                request,
                item.role,
                phase="summary",
                round_index=round_index,
                has_history=has_history,
                objective=item.objective,
            )
            planned_steps = self._build_role_planned_steps(item)
            continuation_brief = self._build_task_continuation_brief(session, item.role, round_index)
            tasks.append(
                SubAgentTask(
                    role=item.role,
                    objective=item.objective,
                    model=summary_model.model,
                    planning_model=plan_model.model,
                    discussion_model=discussion_model.model,
                    summary_model=summary_model.model,
                    round_index=round_index,
                    target_path=request.target_path or "",
                    coordination_focus=item.coordination_focus,
                    collaboration_targets=item.collaboration_targets,
                    expected_evidence=item.expected_evidence,
                    planned_steps=planned_steps,
                    manager_step_total=len(planned_steps),
                    manager_step_completed=0,
                    manager_completion_confirmed=False,
                    stage_goal=item.stage_goal,
                    continuation_brief=continuation_brief,
                )
            )
        return plan_summary, plan_outline, tasks

    def _compose_final_report(self, session: AuditSession) -> str:
        lines = [
            f"# {self._report_title(session)}",
        ]

        manager_highlights = self._collect_manager_highlights(session)
        rce_sections = self._build_rce_assessment_section(session)
        function_sections = self._build_function_report_sections(session, manager_highlights)
        call_chain_sections = self._build_dangerous_call_chain_sections(session, manager_highlights)
        poc_sections = self._build_verified_poc_sections(session)

        if manager_highlights:
            lines.extend(
                [
                    "",
                    "## 关键结论",
                    *[f"- {item}" for item in manager_highlights],
                ]
            )

        if rce_sections:
            lines.extend(["", "## RCE / getshell 结论", *rce_sections])

        if function_sections:
            lines.extend(["", "## 函数级取证结论", *function_sections])

        if call_chain_sections:
            lines.extend(["", "## 危险函数调用链", *call_chain_sections])

        if poc_sections:
            lines.extend(["", "## 已验证 POC", *poc_sections])

        lines.extend(["", "## 子代理归档"])

        for task in session.subagents:
            evidence_status = self._render_tool_digest(task.evidence)
            key_points = self._select_task_key_points(task, manager_highlights, limit=2)
            lines.extend(
                [
                    f"### {task.role}",
                    f"- 轮次: 第 {task.round_index} 轮",
                    f"- 状态: {task.status}",
                    f"- 模型: {task.model}",
                    f"- 干预次数: {len(task.interventions)}",
                    f"- 工具结果: {evidence_status}",
                ]
            )
            if task.container_id:
                lines.append(f"- 容器实例: {task.container_id}")
            if task.error:
                lines.append(f"- 错误: {task.error}")
            for item in key_points:
                lines.append(f"- 已完成结论: {item}")
            lines.append("")
        return "\n".join(lines)

    def _report_title(self, session: AuditSession) -> str:
        raw_title = re.sub(r"\s+", " ", str(session.request.title or "")).strip()
        target_name = Path(session.request.target_path or "").name or "sample"
        if not raw_title or raw_title == "样本初始审计":
            return f"{target_name} 深度审计报告"
        return raw_title

    def _apply_manager_round_review(
        self,
        session: AuditSession,
        round_index: int,
    ) -> tuple[str, list[str], list[str]]:
        round_tasks = [task for task in session.subagents if task.round_index == round_index]
        if not round_tasks:
            return "", [], []

        approved_roles: list[str] = []
        pending_roles: list[str] = []
        review_lines: list[str] = []
        for task in round_tasks:
            total_steps = max(1, task.manager_step_total or len(task.planned_steps) or 1)
            completed_steps = min(total_steps, self._manager_completed_steps_for_task(task))
            task.manager_step_total = total_steps
            task.manager_step_completed = completed_steps
            task.manager_completion_confirmed = (
                task.status == SubAgentStatus.COMPLETED and completed_steps >= total_steps
            )
            missing_steps = task.planned_steps[completed_steps:completed_steps + 2]
            if task.manager_completion_confirmed:
                approved_roles.append(task.role)
                task.manager_review_summary = f"Manager 复核通过：已确认 {completed_steps}/{total_steps} 项计划检查点。"
            else:
                pending_roles.append(task.role)
                if missing_steps:
                    task.manager_review_summary = (
                        f"Manager 复核：已确认 {completed_steps}/{total_steps} 项，仍待补 "
                        + "；".join(missing_steps)
                    )
                else:
                    task.manager_review_summary = f"Manager 复核：已确认 {completed_steps}/{total_steps} 项，仍待补关键证据闭环。"
            review_lines.append(f"{task.role} {completed_steps}/{total_steps}")

        if not review_lines:
            return "", approved_roles, pending_roles

        summary = "Manager 本轮纠偏：" + "；".join(review_lines[:4])
        if pending_roles:
            summary += f"。待补角色：{', '.join(pending_roles[:4])}"
        if approved_roles:
            summary += f"。已通过复核：{', '.join(approved_roles[:4])}"
        return summary, approved_roles, pending_roles

    def _manager_completed_steps_for_task(self, task: SubAgentTask) -> int:
        planned_steps = task.planned_steps or []
        if not planned_steps:
            return 1 if (task.evidence or task.output_summary) else 0

        completed_command_ids = {
            item.command_id
            for item in task.evidence
            if item.status == "completed" and item.command_id
        }
        coordination_events = [
            event
            for event in task.events
            if event.kind in {EventKind.AGENT_MESSAGE_SENT, EventKind.AGENT_MESSAGE_RECEIVED}
        ]
        corpus_parts: list[str] = [
            task.plan_summary or "",
            task.output_summary or "",
            " ".join(task.promoted_notes or []),
            " ".join(item.command_id for item in task.evidence if item.command_id),
            " ".join(item.stdout[:600] for item in task.evidence if item.status == "completed" and item.stdout),
        ]
        corpus = re.sub(r"\s+", " ", " ".join(part for part in corpus_parts if part)).lower()

        completed = 0
        evidence_budget = len(completed_command_ids)
        coordination_budget = len(coordination_events)
        for step in planned_steps:
            if step.startswith("目标闭环："):
                if task.output_summary or completed_command_ids:
                    completed += 1
                continue
            if step.startswith("阶段结论："):
                if self._task_has_stage_boundary(task, corpus):
                    completed += 1
                continue
            if step.startswith("证据产出："):
                if self._planned_step_matches_corpus(step, corpus, completed_command_ids) or evidence_budget > 0:
                    completed += 1
                    evidence_budget = max(0, evidence_budget - 1)
                continue
            if step.startswith("协作广播："):
                if coordination_budget > 0 or (
                    task.status == SubAgentStatus.COMPLETED
                    and not any(item.status in {"failed", "timeout", "unavailable"} for item in task.evidence[-3:])
                ):
                    completed += 1
                    coordination_budget = max(0, coordination_budget - 1)
                continue
            if self._planned_step_matches_corpus(step, corpus, completed_command_ids):
                completed += 1
        return completed

    def _task_has_stage_boundary(self, task: SubAgentTask, corpus: str) -> bool:
        if any(item.command_id == "gdb_poc" and item.status == "completed" for item in task.evidence):
            return True
        return any(
            token in corpus
            for token in (
                "exploit stage",
                "rce",
                "getshell",
                "rip",
                "信息泄露",
                "控制流劫持",
                "未到 rce",
                "未验证",
            )
        )

    def _planned_step_matches_corpus(
        self,
        step: str,
        corpus: str,
        completed_command_ids: set[str],
    ) -> bool:
        command_hints = {
            "函数边界": {"function_disasm", "ida_batch", "angr_cfg"},
            "地址": {"function_disasm", "function_xrefs", "ida_batch", "angr_cfg", "rizin_overview"},
            "调用关系": {"function_xrefs", "rizin_overview", "function_disasm"},
            "参数流": {"function_disasm", "angr_cfg"},
            "危险原语": {"function_disasm", "gdb_poc"},
            "危险导入": {"rizin_overview", "symbol_table"},
            "加固状态": {"checksec"},
            "断点": {"gdb_poc", "gdb_batch"},
            "寄存器": {"gdb_poc", "gdb_batch"},
            "崩溃信号": {"gdb_poc"},
            "运行输出": {"gdb_poc", "afl_showmap_probe"},
            "利用脚本": {"gdb_poc"},
            "poc": {"gdb_poc"},
            "调用点": {"rizin_overview", "function_disasm"},
        }
        normalized_step = re.sub(r"\s+", " ", step).strip().lower()
        if normalized_step and normalized_step in corpus:
            return True
        for keyword, candidates in command_hints.items():
            if keyword in step and completed_command_ids.intersection(candidates):
                return True
        tokens = [
            token.lower()
            for token in re.split(r"[：:，,、；/（）()\s]+", step)
            if len(token.strip()) >= 3
        ]
        for token in tokens:
            if token in corpus:
                return True
        return False

    def _build_subagent_core_notes(self, session: AuditSession) -> list[NoteEntry]:
        return [note.model_copy(deep=True) for note in session.core_notes[:6]]

    def _select_shared_memory_for_task(
        self,
        session: AuditSession,
        task: SubAgentTask,
        *,
        limit: int,
    ) -> list[SharedMemoryEntry]:
        ranked = sorted(
            session.shared_memory,
            key=lambda item: (
                item.priority
                + (120 if item.category == "fixed" else 0)
                + (36 if item.role == task.role else 0)
                + (20 if item.round_index == task.round_index - 1 else 0),
                item.round_index or 0,
                item.created_at,
            ),
            reverse=True,
        )
        selected: list[SharedMemoryEntry] = []
        fixed_selected = 0
        for item in ranked:
            if item.category == "fixed":
                if fixed_selected >= 4:
                    continue
                fixed_selected += 1
            selected.append(item)
            if len(selected) >= limit:
                break
        return list(reversed(selected))

    def _build_reusable_evidence(self, session: AuditSession, task: SubAgentTask) -> list[CommandEvidence]:
        prior_tasks = [
            item
            for item in session.subagents
            if item.round_index < task.round_index and item.evidence
        ]
        if not prior_tasks:
            return []

        pipeline = set(self.toolbox.ROLE_PIPELINES.get(task.role, self.toolbox.ROLE_PIPELINES["triage"]))
        reusable: list[CommandEvidence] = []
        baseline_seen: set[str] = set()
        follow_up_counts: dict[tuple[str, str], int] = {}
        for prior_task in reversed(prior_tasks):
            for evidence in reversed(prior_task.evidence):
                if evidence.status != "completed":
                    continue
                key = (evidence.command_id, prior_task.role)
                if evidence.command_id in pipeline:
                    if evidence.command_id in baseline_seen:
                        continue
                    baseline_seen.add(evidence.command_id)
                    reusable.append(self._clone_reused_evidence(evidence, prior_task))
                    continue
                if evidence.command_id not in {"function_disasm", "function_xrefs", "gdb_poc"}:
                    continue
                limit_per_source = 2 if prior_task.role == task.role else 1
                if follow_up_counts.get(key, 0) >= limit_per_source:
                    continue
                follow_up_counts[key] = follow_up_counts.get(key, 0) + 1
                reusable.append(self._clone_reused_evidence(evidence, prior_task))
        reusable.reverse()
        return reusable[:8]

    def _clone_reused_evidence(self, evidence: CommandEvidence, source_task: SubAgentTask) -> CommandEvidence:
        metadata = dict(evidence.metadata or {})
        metadata.update(
            {
                "reused": True,
                "reused_from_role": source_task.role,
                "reused_from_round": source_task.round_index,
                "reused_from_task_id": source_task.id,
            }
        )
        return evidence.model_copy(deep=True, update={"metadata": metadata})

    def _build_task_continuation_brief(
        self,
        session: AuditSession,
        role: str,
        round_index: int,
    ) -> list[str]:
        brief: list[str] = []
        if round_index <= 1:
            brief.append("首轮先依赖共享记忆中的固定信息，不要重复广播样本基础属性。")
            return brief

        same_role_tasks = [
            item
            for item in session.subagents
            if item.role == role and item.round_index < round_index
        ]
        if same_role_tasks:
            latest = same_role_tasks[-1]
            completed_tools = [item.command_id for item in latest.evidence if item.status == "completed"]
            if completed_tools:
                brief.append(
                    f"优先复用你在第{latest.round_index}轮已完成的工具结果：{', '.join(completed_tools[:6])}"
                )
            key_points = self._select_task_key_points(latest, self._collect_manager_highlights(session), limit=2)
            if key_points:
                brief.append(
                    f"沿用你在第{latest.round_index}轮已确认的结论：{'；'.join(key_points[:2])}"
                )

        relevant_memory = [
            item.content
            for item in self._select_shared_memory_for_manager(session, limit=6)
            if item.role in {None, role} or item.category in {"fixed", "round-summary", "blocker"}
        ]
        if relevant_memory:
            brief.append(f"共享记忆已确认：{'；'.join(relevant_memory[:2])}")

        prior_blockers = [
            f"{task.role}:{item.command_id}={item.status}"
            for task in session.subagents
            if task.round_index < round_index
            for item in task.evidence[-4:]
            if task.role == role and item.status in {"failed", "timeout", "unavailable"}
        ]
        if prior_blockers:
            brief.append(f"本轮只补这些缺口：{'；'.join(prior_blockers[:2])}")
        return self._dedupe_text_items(brief, limit=4)

    async def _record_manager_llm_usage(
        self,
        session_id: str,
        *,
        reply,
        selection: ModelSelection,
        stage: str,
        round_index: int,
    ) -> None:
        event = AuditEvent(
            kind=EventKind.LLM_USAGE_RECORDED,
            message=f"Manager recorded {stage} token usage",
            payload={
                "scope": "manager",
                "stage": stage,
                "round_index": round_index,
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
        async with self._session_lock(session_id):
            try:
                session = self.repository.load_session(session_id)
            except FileNotFoundError:
                return
            self._apply_usage_payload(session.manager_token_usage, event.payload)
            self._recompute_session_token_usage(session)
            session.events.append(event)
            self.repository.save_session(session)
        await self.broker.publish_event(session_id, event)
        await self.broker.publish_snapshot(session)

    def _apply_usage_payload(self, snapshot: TokenUsageSnapshot, payload: dict[str, Any]) -> None:
        snapshot.prompt_tokens += int(payload.get("prompt_tokens", 0) or 0)
        snapshot.completion_tokens += int(payload.get("completion_tokens", 0) or 0)
        snapshot.total_tokens += int(payload.get("total_tokens", 0) or 0)
        snapshot.reasoning_tokens += int(payload.get("reasoning_tokens", 0) or 0)
        snapshot.cached_tokens += int(payload.get("cached_tokens", 0) or 0)
        snapshot.llm_calls += int(payload.get("llm_calls", 0) or 0)

    def _recompute_session_token_usage(self, session: AuditSession) -> None:
        aggregate = TokenUsageSnapshot()
        self._apply_usage_payload(aggregate, session.manager_token_usage.model_dump(mode="json"))
        for task in session.subagents:
            self._apply_usage_payload(aggregate, task.token_usage.model_dump(mode="json"))
        session.token_usage = aggregate

    def _manager_selection(self, session: AuditSession, *, round_index: int) -> ModelSelection:
        request = session.request
        hard_keywords = ("heap", "kernel", "sandbox", "复杂", "链", "格式化字符串", "uaf", "double free")
        unresolved_roles = {
            task.role
            for task in session.subagents
            if task.round_index < round_index and not task.manager_completion_confirmed
        }
        blocker_count = sum(
            1
            for task in session.subagents
            if task.round_index < round_index
            for item in task.evidence[-4:]
            if item.status in {"failed", "timeout", "unavailable"}
        )
        needs_deep_thinking = (
            request.max_subagents > 2
            or request.difficulty == DifficultyHint.HARD
            or any(keyword in request.objective.lower() for keyword in hard_keywords)
            or (round_index == 1 and request.max_subagents > 1)
            or len(unresolved_roles) > 1
            or blocker_count >= 2
        )
        if needs_deep_thinking:
            return ModelSelection(
                model=self.settings.manager_hard_model,
                thinking_enabled=True,
                reasoning_effort="high",
                route_reason="manager-deep-plan",
            )
        return ModelSelection(
            model=self.settings.manager_regular_model,
            thinking_enabled="flash" not in self.settings.manager_regular_model,
            reasoning_effort="medium",
            route_reason="manager-regular-plan",
        )

    def _parse_manager_plan(self, content: str) -> dict[str, Any]:
        text = content.strip()
        fenced_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
        if fenced_match:
            text = fenced_match.group(1)
        elif not text.startswith("{"):
            json_match = re.search(r"(\{.*\})", text, re.DOTALL)
            if json_match:
                text = json_match.group(1)
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return {}
        return payload if isinstance(payload, dict) else {}

    def _coerce_planned_subagents(
        self,
        request: AuditRequest,
        payload: dict[str, Any],
    ) -> list[PlannedSubAgent]:
        max_count = max(1, min(request.max_subagents, self.settings.max_parallel_subagents))
        allowed_roles = {
            "triage",
            "static-analysis",
            "dynamic-analysis",
            "exploitability-review",
            "exploit-strategy",
        }
        global_focus = self._clean_plan_items(payload.get("global_focus"), limit=4)
        parsed_roles = payload.get("roles")
        candidates: list[PlannedSubAgent] = []
        seen_roles: set[str] = set()

        if isinstance(parsed_roles, list):
            for item in parsed_roles:
                if not isinstance(item, dict):
                    continue
                role = str(item.get("role") or "").strip()
                if role not in allowed_roles or role in seen_roles:
                    continue
                seen_roles.add(role)
                objective = str(item.get("objective") or "").strip() or self._default_role_objective(request, role)
                coordination_focus = self._clean_plan_items(item.get("coordination_focus"), limit=4) or list(global_focus)
                collaboration_targets = [
                    target
                    for target in self._clean_plan_items(item.get("collaboration_targets"), limit=4)
                    if target in allowed_roles and target != role
                ]
                expected_evidence = self._clean_plan_items(item.get("expected_evidence"), limit=4)
                stage_goal = self._clean_plan_text(item.get("stage_goal"), limit=160)
                priority_value = item.get("priority")
                try:
                    priority = int(priority_value)
                except (TypeError, ValueError):
                    priority = len(candidates) + 1
                candidates.append(
                    PlannedSubAgent(
                        role=role,
                        objective=objective,
                        coordination_focus=coordination_focus,
                        collaboration_targets=collaboration_targets,
                        expected_evidence=expected_evidence,
                        stage_goal=stage_goal,
                        priority=priority,
                    )
                )

        if not candidates:
            candidates = self._default_planned_subagents(request)

        candidates = sorted(candidates, key=lambda item: (item.priority, item.role))[:max_count]
        if max_count > 1 and len(candidates) == 1:
            fallback_roles = [item.role for item in self._default_planned_subagents(request)]
            for role in fallback_roles:
                if role == candidates[0].role:
                    continue
                candidates.append(
                    PlannedSubAgent(
                        role=role,
                        objective=self._default_role_objective(request, role),
                        coordination_focus=list(global_focus) or [request.objective[:120]],
                        collaboration_targets=[candidates[0].role],
                        expected_evidence=self._default_expected_evidence(role),
                        stage_goal=self._default_stage_goal(role),
                        priority=len(candidates) + 1,
                    )
                )
                break

        selected_roles = [item.role for item in candidates]
        normalized: list[PlannedSubAgent] = []
        for item in candidates[:max_count]:
            targets = [target for target in item.collaboration_targets if target in selected_roles and target != item.role]
            if not targets and len(selected_roles) > 1:
                targets = [role for role in selected_roles if role != item.role]
            expected_evidence = item.expected_evidence or self._default_expected_evidence(item.role)
            stage_goal = item.stage_goal or self._default_stage_goal(item.role)
            normalized.append(
                PlannedSubAgent(
                    role=item.role,
                    objective=item.objective,
                    coordination_focus=item.coordination_focus or list(global_focus),
                    collaboration_targets=targets,
                    expected_evidence=expected_evidence,
                    stage_goal=stage_goal,
                    expected_evidence_is_default=not bool(item.expected_evidence),
                    stage_goal_is_default=not bool(item.stage_goal),
                    priority=item.priority,
                )
            )
        return normalized

    def _default_planned_subagents(self, request: AuditRequest) -> list[PlannedSubAgent]:
        if request.difficulty == DifficultyHint.HARD:
            roles = ["triage", "static-analysis", "dynamic-analysis", "exploit-strategy"]
        elif request.difficulty == DifficultyHint.ROUTINE:
            roles = ["triage", "static-analysis", "exploitability-review"]
        else:
            roles = ["triage", "static-analysis", "exploitability-review"]
            if any(keyword in request.objective.lower() for keyword in ("heap", "kernel", "sandbox", "复杂", "链")):
                roles.append("dynamic-analysis")

        planned: list[PlannedSubAgent] = []
        for index, role in enumerate(roles, start=1):
            planned.append(
                PlannedSubAgent(
                    role=role,
                    objective=self._default_role_objective(request, role),
                    coordination_focus=self._default_coordination_focus(role),
                    collaboration_targets=[target for target in roles if target != role],
                    expected_evidence=self._default_expected_evidence(role),
                    stage_goal=self._default_stage_goal(role),
                    expected_evidence_is_default=False,
                    stage_goal_is_default=False,
                    priority=index,
                )
            )
        return planned[: max(1, min(request.max_subagents, self.settings.max_parallel_subagents))]

    def _default_role_objective(self, request: AuditRequest, role: str) -> str:
        role_objectives = {
            "triage": f"{request.objective}。先确认样本属性、加固状态、危险导入与初始高风险函数，并把关键函数名和地址广播给同伴。",
            "static-analysis": f"{request.objective}。恢复函数边界、调用关系和关键参数流，优先验证同伴提到的高风险函数。",
            "dynamic-analysis": f"{request.objective}。确认运行期装载、调试入口和执行阻塞点，并回传会影响利用链判断的运行期事实。",
            "exploitability-review": f"{request.objective}。结合字符串、CFG 与调试信息判断输入面、可控数据和危险原语是否成立。",
            "exploit-strategy": f"{request.objective}。围绕已识别输入点、危险调用和保护机制，收束到函数级利用链结论。",
        }
        return role_objectives.get(role, f"{request.objective} [{role}]")

    def _default_coordination_focus(self, role: str) -> list[str]:
        defaults = {
            "triage": ["危险导入", "疑似高风险函数", "加固状态是否影响利用"],
            "static-analysis": ["函数边界", "关键调用点", "参数与缓冲区关系"],
            "dynamic-analysis": ["运行期阻塞", "调试入口", "动态装载事实"],
            "exploitability-review": ["输入面", "可控数据流", "危险原语是否成立"],
            "exploit-strategy": ["利用链前提", "可写 GOT/固定基址", "函数级漏洞闭环"],
        }
        return defaults.get(role, ["关键函数", "证据缺口"])

    def _clean_plan_items(self, value: Any, *, limit: int) -> list[str]:
        if not isinstance(value, list):
            return []
        cleaned: list[str] = []
        for item in value:
            text = re.sub(r"\s+", " ", str(item or "")).strip()
            if not text or text in cleaned:
                continue
            cleaned.append(text[:180])
            if len(cleaned) >= limit:
                break
        return cleaned

    def _clean_plan_text(self, value: Any, *, limit: int) -> str:
        text = re.sub(r"\s+", " ", str(value or "")).strip()
        return text[:limit] if text else ""

    def _default_stage_goal(self, role: str) -> str:
        defaults = {
            "triage": "优先确认当前仍处于未验证/疑似阶段，还是已经能明确到信息泄露或溢出原语。",
            "static-analysis": "把 exploit stage 对应的关键函数、调用点和危险原语下沉到函数级证据。",
            "dynamic-analysis": "优先把动态结论推进到信息泄露、栈覆盖或 RIP 可控中的明确一级。",
            "exploitability-review": "明确当前最多推进到哪一级，不能把未验证原语误写成 RCE / getshell。",
            "exploit-strategy": "围绕已验证原语判断当前止步于未验证、信息泄露、控制流劫持还是更高阶段。",
        }
        return defaults.get(role, "明确当前 exploit stage 的真实边界。")

    def _default_expected_evidence(self, role: str) -> list[str]:
        defaults = {
            "triage": ["样本加固状态", "危险导入与调用点", "首批重点函数与地址"],
            "static-analysis": ["函数边界与地址", "调用关系与参数流", "危险原语的函数级解释"],
            "dynamic-analysis": ["GDB 断点/寄存器快照", "原生运行输出或崩溃信号", "exploit stage 的动态边界"],
            "exploitability-review": ["原语成立/不成立的证据", "RCE / getshell 边界说明", "关键工具失败的影响"],
            "exploit-strategy": ["PoC 触发命令", "利用脚本片段", "当前卡住的原语或边界"],
        }
        return list(defaults.get(role, ["函数级证据", "动态边界", "利用结论"]))

    def _build_role_planned_steps(self, item: PlannedSubAgent) -> list[str]:
        steps: list[str] = []
        seen: set[str] = set()

        def append_step(text: str) -> None:
            normalized = re.sub(r"\s+", " ", str(text or "")).strip()
            if not normalized or normalized in seen:
                return
            seen.add(normalized)
            steps.append(normalized[:180])

        append_step(f"目标闭环：{self._clean_plan_text(item.objective, limit=140)}")
        if item.stage_goal and not item.stage_goal_is_default:
            append_step(f"阶段结论：{self._clean_plan_text(item.stage_goal, limit=140)}")
        if not item.expected_evidence_is_default:
            for evidence in item.expected_evidence[:4]:
                append_step(f"证据产出：{evidence}")
        for focus in item.coordination_focus[:2]:
            append_step(f"协作广播：{focus}")
        return steps[:8] or ["目标闭环：完成本轮函数级与利用边界取证。"]

    def _build_manager_plan_outline(
        self,
        raw_content: str,
        payload: dict[str, Any],
        planned_subagents: list[PlannedSubAgent],
    ) -> ManagerPlanOutline:
        summary = self._clean_plan_text(payload.get("strategy_summary"), limit=260)
        if not summary:
            summary = re.sub(r"\s+", " ", raw_content).strip()[:260]

        focus_items = self._clean_plan_items(payload.get("global_focus"), limit=4)
        success_criteria = self._clean_plan_items(payload.get("success_criteria"), limit=4)
        if not success_criteria:
            success_criteria = [
                "锁定输入入口、危险函数、调用关系与关键地址。",
                "形成至少一条动态取证链，并明确 exploit stage 是否已推进。",
                "最终报告必须落到函数级、动态证据和 RCE / getshell 边界。",
            ]

        phase_plan: list[ManagerPlanPhase] = []
        raw_phase_plan = payload.get("phase_plan")
        if isinstance(raw_phase_plan, list):
            for index, item in enumerate(raw_phase_plan[:4], start=1):
                if not isinstance(item, dict):
                    continue
                phase_name = self._clean_plan_text(
                    item.get("phase") or item.get("title") or f"阶段 {index}",
                    limit=64,
                ) or f"阶段 {index}"
                goal = self._clean_plan_text(item.get("goal"), limit=180)
                owner_roles = [
                    role
                    for role in self._clean_plan_items(item.get("owner_roles"), limit=4)
                    if role in {task.role for task in planned_subagents}
                ]
                exit_criteria = self._clean_plan_items(item.get("exit_criteria"), limit=3)
                if goal:
                    phase_plan.append(
                        ManagerPlanPhase(
                            phase=phase_name,
                            goal=goal,
                            owner_roles=owner_roles,
                            exit_criteria=exit_criteria,
                        )
                    )

        if not phase_plan:
            phase_plan = [
                ManagerPlanPhase(
                    phase="阶段 1",
                    goal="先锁定样本属性、危险函数、关键调用点与基础 exploit stage 方向。",
                    owner_roles=[item.role for item in planned_subagents[:2]],
                    exit_criteria=["拿到入口函数/危险调用的函数级候选。"],
                ),
                ManagerPlanPhase(
                    phase="阶段 2",
                    goal="让静态与动态证据交叉验证原语是否真实成立。",
                    owner_roles=[item.role for item in planned_subagents[:3]],
                    exit_criteria=["至少形成一条带动态证据的原语判断链。"],
                ),
                ManagerPlanPhase(
                    phase="阶段 3",
                    goal="收束到函数级结论、PoC 与 RCE / getshell 边界。",
                    owner_roles=[item.role for item in planned_subagents],
                    exit_criteria=["报告能明确写清当前止步边界。"],
                ),
            ]

        risk_watchpoints = self._clean_plan_items(payload.get("risk_watchpoints"), limit=4)
        if not risk_watchpoints:
            risk_watchpoints = [
                "避免把静态迹象误写成已验证漏洞或已 getshell。",
                "若关键工具失败，必须在报告里显式写出对 exploit stage 的影响。",
            ]

        roles = [
            ManagerPlanRole(
                role=item.role,
                objective=item.objective,
                coordination_focus=item.coordination_focus,
                collaboration_targets=item.collaboration_targets,
                expected_evidence=item.expected_evidence,
                planned_steps=self._build_role_planned_steps(item),
                stage_goal=item.stage_goal,
                priority=item.priority,
            )
            for item in planned_subagents
        ]

        return ManagerPlanOutline(
            strategy_summary=summary or "Manager 已完成深度调度规划。",
            global_focus=focus_items,
            success_criteria=success_criteria,
            phase_plan=phase_plan,
            risk_watchpoints=risk_watchpoints,
            roles=roles,
        )

    def _render_manager_plan_summary(self, plan: ManagerPlanOutline) -> str:
        lines = [
            "## 总体规划",
            f"- 策略摘要: {plan.strategy_summary or 'Manager 已完成深度调度规划。'}",
        ]
        if plan.global_focus:
            lines.extend(
                [
                    "## 跨角色重点",
                    *[f"- {item}" for item in plan.global_focus],
                ]
            )
        if plan.success_criteria:
            lines.extend(
                [
                    "## 成功判据",
                    *[f"- {item}" for item in plan.success_criteria],
                ]
            )
        if plan.phase_plan:
            lines.append("## 分阶段执行")
        for item in plan.phase_plan[:4]:
            lines.extend(
                [
                    f"### {item.phase}",
                    f"- 阶段目标: {item.goal}",
                    (
                        f"- 主责角色: {', '.join(item.owner_roles)}"
                        if item.owner_roles
                        else "- 主责角色: 全体协同"
                    ),
                ]
            )
            for criterion in item.exit_criteria[:3]:
                lines.append(f"- 阶段退出条件: {criterion}")
        if plan.risk_watchpoints:
            lines.extend(
                [
                    "## 风险观察",
                    *[f"- {item}" for item in plan.risk_watchpoints],
                ]
            )
        if plan.roles:
            lines.append("## 角色分工")
        for item in plan.roles[:6]:
            lines.extend(
                [
                    f"### {item.role}",
                    f"- 本轮目标: {item.objective}",
                    f"- 阶段目标: {item.stage_goal or '明确当前 exploit stage 边界。'}",
                    (
                        f"- Manager 计划步数: {len(item.planned_steps)}"
                        if item.planned_steps
                        else "- Manager 计划步数: 0"
                    ),
                    (
                        f"- 广播重点: {'；'.join(item.coordination_focus[:4])}"
                        if item.coordination_focus
                        else "- 广播重点: 暂无"
                    ),
                    (
                        f"- 预期证据: {'；'.join(item.expected_evidence[:4])}"
                        if item.expected_evidence
                        else "- 预期证据: 暂无"
                    ),
                    (
                        f"- 协作对象: {', '.join(item.collaboration_targets)}"
                        if item.collaboration_targets
                        else "- 协作对象: 暂无"
                    ),
                ]
            )
            for planned_step in item.planned_steps[:4]:
                lines.append(f"- 计划检查点: {planned_step}")
        return "\n".join(lines)

    def _highlight_key(self, note: str) -> str:
        lowered = note.lower()
        if "格式化字符串" in note:
            return "format-string"
        if any(token in lowered for token in ("my_gadget", "rop gadget", "pop rdi", "gadget")):
            return "gadget"
        if any(token in lowered for token in ("no canary", "no pie")) or "固定基址" in note or "利用条件" in note:
            return "mitigations"
        if "溢出" in note:
            return "overflow"
        return note[:96]

    def _collect_manager_highlights(self, session: AuditSession) -> list[str]:
        manager_highlights: list[str] = []
        seen_highlight_keys: set[str] = set()
        for task in session.subagents:
            for note in task.promoted_notes:
                if self._is_incomplete_report_line(note):
                    continue
                key = self._highlight_key(note)
                if key in seen_highlight_keys:
                    continue
                seen_highlight_keys.add(key)
                manager_highlights.append(note)
                if len(manager_highlights) >= 4:
                    return manager_highlights
        return manager_highlights

    def _build_function_report_sections(
        self,
        session: AuditSession,
        manager_highlights: list[str],
    ) -> list[str]:
        entries: dict[str, FunctionReportEntry] = {}
        for task in session.subagents:
            for evidence in task.evidence:
                if evidence.status != "completed":
                    continue
                payload = self._load_json_payload(evidence.stdout)
                if evidence.command_id == "function_disasm" and isinstance(payload, dict):
                    self._ingest_function_disasm(entries, task.role, payload)
                elif evidence.command_id == "function_xrefs" and isinstance(payload, dict):
                    self._ingest_function_xrefs(entries, task.role, payload)
                elif evidence.command_id == "rizin_overview" and isinstance(payload, dict):
                    self._ingest_rizin_overview(entries, task.role, payload)
                elif evidence.command_id == "ida_batch" and isinstance(payload, dict):
                    self._ingest_ida_preview(entries, task.role, payload)
                elif evidence.command_id == "angr_cfg" and isinstance(payload, dict):
                    self._ingest_angr_preview(entries, task.role, payload)
                elif evidence.command_id == "gdb_poc" and isinstance(payload, dict):
                    self._ingest_gdb_poc(entries, task.role, payload)

        self._apply_manager_highlight_overrides(entries, manager_highlights)
        ranked = sorted(
            entries.values(),
            key=lambda item: (
                item.score,
                len(item.issue_lines),
                len(item.fact_lines),
                item.address or "",
                item.name,
            ),
            reverse=True,
        )
        rendered: list[str] = []
        for entry in ranked[:4]:
            title = entry.name if not entry.address else f"{entry.name} @ {entry.address}"
            call_chain_lines = self._render_entry_call_chains(entry)
            rendered.extend(
                [
                    f"### {title}",
                    f"- 角色覆盖: {', '.join(sorted(entry.roles)) or '未知'}",
                    f"- 证据来源: {', '.join(sorted(entry.tools)) or '未知'}",
                ]
            )
            for insight in call_chain_lines[:2]:
                rendered.append(f"- 危险调用链: {insight}")
            for insight in (entry.issue_lines + entry.caller_lines + entry.fact_lines)[:5]:
                rendered.append(f"- {insight}")
            rendered.append("")

        while rendered and rendered[-1] == "":
            rendered.pop()
        return rendered

    def _build_dangerous_call_chain_sections(
        self,
        session: AuditSession,
        manager_highlights: list[str],
    ) -> list[str]:
        entries: dict[str, FunctionReportEntry] = {}
        for task in session.subagents:
            for evidence in task.evidence:
                if evidence.status != "completed":
                    continue
                payload = self._load_json_payload(evidence.stdout)
                if evidence.command_id == "function_disasm" and isinstance(payload, dict):
                    self._ingest_function_disasm(entries, task.role, payload)
                elif evidence.command_id == "function_xrefs" and isinstance(payload, dict):
                    self._ingest_function_xrefs(entries, task.role, payload)
                elif evidence.command_id == "rizin_overview" and isinstance(payload, dict):
                    self._ingest_rizin_overview(entries, task.role, payload)
                elif evidence.command_id == "gdb_poc" and isinstance(payload, dict):
                    self._ingest_gdb_poc(entries, task.role, payload)

        self._apply_manager_highlight_overrides(entries, manager_highlights)
        rendered: list[str] = []
        seen: set[str] = set()
        ranked = sorted(entries.values(), key=lambda item: item.score, reverse=True)
        for entry in ranked:
            for chain in self._render_entry_call_chains(entry)[:3]:
                if chain in seen:
                    continue
                seen.add(chain)
                rendered.append(f"- {chain}")
                if len(rendered) >= 6:
                    return rendered
        return rendered

    def _build_rce_assessment_section(self, session: AuditSession) -> list[str]:
        payloads = self._collect_rce_payloads(session)
        if payloads:
            ranked = sorted(
                payloads,
                key=lambda item: (
                    self._rce_stage_rank(item["stage_id"]),
                    1 if item["validated"] else 0,
                    item["function_address"] or "",
                    item["function_name"],
                ),
                reverse=True,
            )
            primary = ranked[0]
            primary_assessment = primary["assessment"]
            rendered = [
                f"- 全局分级: {primary['stage_label']}",
                f"- 汇总结论: {self._compact_fact_text(primary_assessment.get('verdict'))}",
            ]
            primary_boundary = self._compact_fact_text(primary_assessment.get("boundary"))
            if primary_boundary:
                rendered.append(f"- 当前边界: {primary_boundary}")
            primary_script = primary.get("exploit_script") or {}
            if isinstance(primary_script, dict) and str(primary_script.get("content") or "").strip():
                script_language = self._compact_fact_text(primary_script.get("language")) or "python"
                script_filename = self._compact_fact_text(primary_script.get("filename"))
                script_label = f" {script_language} 利用脚本"
                if script_filename:
                    script_label += f" `{script_filename}`"
                rendered.append(f"- PoC 产物: 已生成可复现的{script_label}，不再只停留在 GDB 调试命令。")
            rendered.append(
                f"- 证据闭环: {primary['function_title']} / {primary['issue_type']} / {primary['stage_label']}"
            )

            for item in ranked[:3]:
                details: list[str] = [item["stage_label"]]
                dynamic_evidence = item["assessment"].get("dynamic_evidence") or []
                if isinstance(dynamic_evidence, list):
                    evidence_preview = [self._compact_fact_text(value) for value in dynamic_evidence if value]
                    if evidence_preview:
                        details.append(f"动态依据: {'；'.join(evidence_preview[:2])}")
                if item["gdb_observation"].get("control_offset") is not None:
                    details.append(f"RIP 偏移={item['gdb_observation']['control_offset']}")
                if item["native_probe"].get("signal"):
                    details.append(f"原生信号={item['native_probe']['signal']}")
                rendered.append(f"- {item['function_title']}: {'；'.join(details)}")
            return rendered

        static_candidates = self._collect_static_rce_candidates(session)
        if static_candidates:
            joined = "；".join(static_candidates[:3])
            return [
                "- 全局分级: 未验证到 RCE / getshell",
                f"- 当前已确认: {joined}",
                "- 动态边界: 本轮没有 GDB PoC 把原语推进到命令执行或 shell 交互。",
            ]

        return [
            "- 全局分级: 未验证到 RCE / getshell",
            "- 当前已完成取证未形成可落到 RCE 的动态证据链。",
        ]

    def _collect_rce_payloads(self, session: AuditSession) -> list[dict[str, Any]]:
        collected: list[dict[str, Any]] = []
        for task in session.subagents:
            for evidence in task.evidence:
                if evidence.command_id != "gdb_poc":
                    continue
                payload = self._load_json_payload(evidence.stdout)
                if not isinstance(payload, dict):
                    continue
                function = payload.get("function") or {}
                if not isinstance(function, dict):
                    function = {}
                assessment = payload.get("rce_assessment") or {}
                if not isinstance(assessment, dict):
                    assessment = {}
                if not assessment:
                    assessment = self._synthesize_rce_assessment_from_poc_payload(payload)
                function_name = str(function.get("name") or "unknown")
                function_address = self._normalize_address(function.get("address"))
                function_title = function_name if not function_address else f"{function_name} @ {function_address}"
                collected.append(
                    {
                        "task_role": task.role,
                        "validated": bool(payload.get("validated")),
                        "issue_type": str(payload.get("issue_type") or "unknown"),
                        "function_name": function_name,
                        "function_address": function_address,
                        "function_title": function_title,
                        "stage_id": str(assessment.get("stage_id") or "not-validated"),
                        "stage_label": self._compact_fact_text(assessment.get("stage_label")) or "未验证到可利用阶段",
                        "assessment": assessment,
                        "gdb_observation": payload.get("gdb_observation") if isinstance(payload.get("gdb_observation"), dict) else {},
                        "native_probe": payload.get("native_probe") if isinstance(payload.get("native_probe"), dict) else {},
                        "exploit_script": payload.get("exploit_script") if isinstance(payload.get("exploit_script"), dict) else {},
                    }
                )
        return collected

    def _synthesize_rce_assessment_from_poc_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        issue_type = str(payload.get("issue_type") or "unknown")
        validated = bool(payload.get("validated"))
        gdb_observation = payload.get("gdb_observation") or {}
        native_probe = payload.get("native_probe") or {}
        command_output = self._compact_fact_text(payload.get("command_output"))
        shell_observation = self._compact_fact_text(
            payload.get("shell_observation") or payload.get("shell_prompt") or payload.get("shell_banner")
        )
        dynamic_evidence = [
            self._compact_fact_text(value)
            for value in (
                gdb_observation.get("breakpoint_line"),
                gdb_observation.get("argument_line"),
                gdb_observation.get("signal_line"),
                native_probe.get("probe_line"),
                native_probe.get("signal"),
                command_output,
                shell_observation,
            )
            if value
        ]

        if shell_observation:
            return {
                "stage_id": "getshell",
                "stage_label": "已验证 getshell",
                "rce_reached": True,
                "getshell_reached": True,
                "verdict": "动态证据已经出现 shell 交互或 shell 提示，当前结论可推进到 getshell。",
                "boundary": "已越过 RCE 阶段并进入 shell 交互。",
                "dynamic_evidence": dynamic_evidence[:4],
            }

        if command_output:
            return {
                "stage_id": "code-exec",
                "stage_label": "已验证 RCE，未确认 getshell",
                "rce_reached": True,
                "getshell_reached": False,
                "verdict": "动态证据已经出现命令执行回显，当前结论可推进到 RCE，但尚未确认 shell 交互。",
                "boundary": "尚未观察到稳定 shell 提示或交互式 shell 回显。",
                "dynamic_evidence": dynamic_evidence[:4],
            }

        if issue_type == "format-string":
            return {
                "stage_id": "info-leak" if validated else "not-validated",
                "stage_label": "已验证信息泄露，未到 RCE / getshell" if validated else "未验证到可利用阶段",
                "rce_reached": False,
                "getshell_reached": False,
                "verdict": (
                    "当前动态证据已证明格式串造成地址泄露，但未看到写原语、控制流劫持、命令执行或 getshell。"
                    if validated
                    else "当前格式串只停留在怀疑点，尚未通过动态调试把 exploit stage 推进到信息泄露。"
                ),
                "boundary": "未观察到写原语、控制流劫持、命令执行或 shell 交互。",
                "dynamic_evidence": dynamic_evidence[:3],
            }

        control_offset = gdb_observation.get("control_offset")
        if issue_type == "overflow-candidate":
            if isinstance(control_offset, int):
                stage_id = "control-hijack"
                stage_label = "已验证返回地址可控，已到控制流劫持阶段，未到 RCE / getshell"
                verdict = "动态调试已把溢出推进到 RIP 可控，但尚未观察到命令执行或 getshell。"
                boundary = "当前没有 system/execve 调用结果或 shell 交互回显。"
            elif gdb_observation.get("signal_line") or native_probe.get("signal"):
                stage_id = "crash-only"
                stage_label = "已验证崩溃，尚未证明控制流劫持"
                verdict = "动态调试已确认溢出可触发异常退出，但尚未证明 RIP 可控。"
                boundary = "当前不能把结论推进到 RCE / getshell。"
            else:
                stage_id = "not-validated"
                stage_label = "未验证到可利用阶段"
                verdict = "当前只有静态溢出迹象，尚未拿到稳定的动态 exploit stage 证据。"
                boundary = "当前不能把结论推进到控制流劫持、RCE 或 getshell。"
            return {
                "stage_id": stage_id,
                "stage_label": stage_label,
                "rce_reached": False,
                "getshell_reached": False,
                "verdict": verdict,
                "boundary": boundary,
                "dynamic_evidence": dynamic_evidence[:3],
            }

        return {
            "stage_id": "not-validated",
            "stage_label": "未验证到可利用阶段",
            "rce_reached": False,
            "getshell_reached": False,
            "verdict": "当前 PoC 结果未提供足够字段，无法把结论推进到 RCE / getshell。",
            "boundary": "缺少 exploit stage 所需的动态调试细节。",
            "dynamic_evidence": dynamic_evidence[:3],
        }

    def _collect_static_rce_candidates(self, session: AuditSession) -> list[str]:
        candidates: list[str] = []
        seen: set[str] = set()
        for task in session.subagents:
            for evidence in task.evidence:
                if evidence.command_id != "function_disasm" or evidence.status != "completed":
                    continue
                payload = self._load_json_payload(evidence.stdout)
                if not isinstance(payload, dict):
                    continue
                for function in payload.get("functions", []) or []:
                    if not isinstance(function, dict):
                        continue
                    function_name = str(function.get("name") or "unknown")
                    function_address = self._normalize_address(function.get("address")) or "unknown"
                    for call_site in function.get("call_sites", []) or []:
                        if not isinstance(call_site, dict):
                            continue
                        issue = call_site.get("issue")
                        if not isinstance(issue, dict):
                            continue
                        issue_type = str(issue.get("type") or "").strip()
                        if not issue_type:
                            continue
                        evidence_text = self._compact_fact_text(issue.get("evidence"))
                        label = (
                            f"{function_name} @ {function_address} 仅静态识别到 {issue_type}"
                            + (f"（{evidence_text}）" if evidence_text else "")
                        )
                        if label not in seen:
                            seen.add(label)
                            candidates.append(label)
        return candidates

    def _rce_stage_rank(self, stage_id: str) -> int:
        ranks = {
            "getshell": 5,
            "code-exec": 4,
            "control-hijack": 3,
            "stack-overwrite": 2,
            "info-leak": 1,
            "crash-only": 0,
            "not-validated": -1,
        }
        return ranks.get(stage_id, -1)

    def _build_verified_poc_sections(self, session: AuditSession) -> list[str]:
        rendered: list[str] = []
        seen: set[str] = set()

        for task in session.subagents:
            for evidence in task.evidence:
                if evidence.command_id != "gdb_poc" or evidence.status != "completed":
                    continue
                payload = self._load_json_payload(evidence.stdout)
                if not isinstance(payload, dict) or not payload.get("validated"):
                    continue

                function = payload.get("function") or {}
                function_name = str(function.get("name") or "unknown")
                function_address = str(function.get("address") or "").strip()
                issue_type = str(payload.get("issue_type") or "unknown")
                dedupe_key = f"{function_name}@{function_address}:{issue_type}"
                if dedupe_key in seen:
                    continue
                seen.add(dedupe_key)

                title = function_name if not function_address else f"{function_name} @ {function_address}"
                rendered.extend(
                    [
                        f"### {title}",
                        f"- PoC 类型: {issue_type}",
                    ]
                )

                assessment = payload.get("rce_assessment") or {}
                if not isinstance(assessment, dict):
                    assessment = {}
                if not assessment:
                    assessment = self._synthesize_rce_assessment_from_poc_payload(payload)
                if isinstance(assessment, dict):
                    stage_label = self._compact_fact_text(assessment.get("stage_label"))
                    verdict = self._compact_fact_text(assessment.get("verdict"))
                    boundary = self._compact_fact_text(assessment.get("boundary"))
                    dynamic_evidence = assessment.get("dynamic_evidence") or []
                    if stage_label:
                        rendered.append(f"- RCE 分级: {stage_label}")
                    if verdict:
                        rendered.append(f"- 结论: {verdict}")
                    if dynamic_evidence and isinstance(dynamic_evidence, list):
                        evidence_preview = [self._compact_fact_text(value) for value in dynamic_evidence if value]
                        if evidence_preview:
                            rendered.append(f"- 动态调试证据: {'；'.join(evidence_preview[:2])}")
                    if boundary:
                        rendered.append(f"- 当前边界: {boundary}")
                    rendered.append(
                        f"- 证据链: 函数级原语 `{issue_type}` -> GDB 断点/运行探针 -> {stage_label or '未验证到可利用阶段'}"
                    )

                exploit_script = payload.get("exploit_script") or {}
                script_content = self._normalize_poc_text_for_report(
                    str(exploit_script.get("content") or ""),
                    session.request.target_path or "",
                )
                script_language = self._compact_fact_text(exploit_script.get("language")) or "python"
                script_filename = self._compact_fact_text(exploit_script.get("filename")) or f"exploit_{issue_type}.py"
                if script_content.strip():
                    rendered.extend(
                        [
                            f"- 漏洞利用脚本 PoC: `{script_filename}`",
                            f"```{script_language}",
                            script_content.rstrip(),
                            "```",
                        ]
                    )

                gdb_observation = payload.get("gdb_observation") or {}
                argument_line = self._compact_fact_text(gdb_observation.get("argument_line"))
                breakpoint_line = self._compact_fact_text(gdb_observation.get("breakpoint_line"))
                signal_line = self._compact_fact_text(gdb_observation.get("signal_line"))
                rip_line = self._compact_fact_text(gdb_observation.get("rip_line"))
                control_offset = gdb_observation.get("control_offset")
                if breakpoint_line:
                    rendered.append(f"- GDB 断点命中: `{breakpoint_line}`")
                if argument_line:
                    rendered.append(f"- GDB 实参取证: `{argument_line}`")
                if signal_line:
                    rendered.append(f"- GDB 崩溃信号: `{signal_line}`")
                if rip_line:
                    rendered.append(f"- GDB RIP 快照: `{rip_line}`")
                if isinstance(control_offset, int):
                    rendered.append(f"- GDB RIP 偏移: `{control_offset}`")

                poc = payload.get("poc") or {}
                poc_command = self._normalize_poc_command_for_report(
                    self._compact_fact_text(poc.get("command")),
                    session.request.target_path or "",
                )
                if poc_command:
                    rendered.append(f"- 触发命令: `{poc_command}`")

                native_probe = payload.get("native_probe") or {}
                probe_line = self._compact_fact_text(native_probe.get("probe_line"))
                stdout_preview = self._compact_fact_text(native_probe.get("stdout_preview"))
                signal_preview = self._compact_fact_text(native_probe.get("signal"))
                command_output = self._compact_fact_text(payload.get("command_output"))
                shell_observation = self._compact_fact_text(
                    payload.get("shell_observation") or payload.get("shell_prompt") or payload.get("shell_banner")
                )
                runtime_excerpt = probe_line or stdout_preview
                if runtime_excerpt:
                    rendered.append(f"- 运行输出摘录: `{runtime_excerpt[:220]}`")
                if signal_preview:
                    rendered.append(f"- 原生运行信号: `{signal_preview}`")
                if command_output:
                    rendered.append(f"- 命令执行回显: `{command_output[:220]}`")
                if shell_observation:
                    rendered.append(f"- shell 观测: `{shell_observation[:220]}`")

                rendered.append("")

        while rendered and rendered[-1] == "":
            rendered.pop()
        return rendered

    def _normalize_poc_command_for_report(self, command: str, target_path: str) -> str:
        normalized = command.strip()
        if not normalized or not target_path:
            return normalized
        return self._normalize_poc_text_for_report(normalized, target_path)

    def _normalize_poc_text_for_report(self, text: str, target_path: str) -> str:
        normalized = text
        if not normalized or not target_path:
            return normalized
        quoted_target = shlex.quote(target_path)
        normalized = re.sub(r"/runtime/inputs/[^\s`'\"()<>]+", quoted_target, normalized)
        normalized = re.sub(r"/workspace/[^\s`'\"()<>]+", quoted_target, normalized)
        return normalized

    def _apply_manager_highlight_overrides(
        self,
        entries: dict[str, FunctionReportEntry],
        manager_highlights: list[str],
    ) -> None:
        format_string_refuted = any(
            "排除格式化字符串" in item or ("误报" in item and "printf" in item and "puts" in item)
            for item in manager_highlights
        )
        info_leak_highlights = [
            item
            for item in manager_highlights
            if "信息泄露" in item or ("泄漏" in item and "libc" in item)
        ]
        main_entry = self._find_function_entry(entries, "main")

        if format_string_refuted:
            for entry in entries.values():
                entry.issue_lines = [
                    line
                    for line in entry.issue_lines
                    if "格式串" not in line and "格式化字符串" not in line
                ]
            if main_entry is not None:
                self._append_unique(
                    main_entry.fact_lines,
                    "`Manager` 结合 triage 复核后确认：此前基于 `function_disasm` 的格式串告警属于 `puts/printf` 符号误判，不能据此认定格式化字符串漏洞。",
                )
                main_entry.score += 8

        if main_entry is not None:
            for item in info_leak_highlights[:2]:
                self._append_unique(
                    main_entry.issue_lines,
                    f"`Manager` 综合已完成结论确认：{self._compact_fact_text(item)}",
                )
                main_entry.score += 10

    def _render_entry_call_chains(self, entry: FunctionReportEntry) -> list[str]:
        entry_title = entry.name if not entry.address else f"{entry.name}@{entry.address}"
        rendered: list[str] = []
        seen: set[str] = set()

        caller_titles = [
            caller_name if not caller_addr else f"{caller_name}@{caller_addr}"
            for caller_name, caller_addr in entry.caller_refs[:3]
        ]
        if not caller_titles:
            caller_titles = [""]

        if entry.dangerous_call_refs:
            for caller_title in caller_titles:
                for target, from_addr in entry.dangerous_call_refs[:4]:
                    chain = f"{entry_title} -> {target}@{from_addr}" if from_addr else f"{entry_title} -> {target}"
                    if caller_title:
                        chain = f"{caller_title} -> {chain}"
                    if chain not in seen:
                        seen.add(chain)
                        rendered.append(chain)
        else:
            for caller_title in caller_titles:
                if not caller_title:
                    continue
                if caller_title not in seen:
                    seen.add(caller_title)
                    rendered.append(f"{caller_title} -> {entry_title}")
        return rendered

    def _is_dangerous_call_target(self, target: str) -> bool:
        normalized = (target or "").lower()
        return any(
            token in normalized
            for token in (
                "system",
                "gets",
                "printf",
                "fprintf",
                "sprintf",
                "snprintf",
                "scanf",
                "sscanf",
                "read",
                "recv",
                "fgets",
                "strcpy",
                "strncpy",
                "memcpy",
                "memmove",
                "popen",
                "execve",
                "execl",
                "execvp",
            )
        )

    def _ingest_function_disasm(
        self,
        entries: dict[str, FunctionReportEntry],
        role: str,
        payload: dict[str, Any],
    ) -> None:
        for item in payload.get("functions", []) or []:
            if not isinstance(item, dict):
                continue
            entry = self._upsert_function_entry(entries, item.get("name"), item.get("address"), role, "function_disasm")
            stack_frame = item.get("stack_frame_bytes")
            call_sites = item.get("call_sites") or []
            interesting_calls: list[str] = []
            for call_site in call_sites:
                if not isinstance(call_site, dict):
                    continue
                target = str(call_site.get("target") or "")
                from_addr = str(call_site.get("from") or "")
                if target and len(interesting_calls) < 3:
                    interesting_calls.append(f"{target}@{from_addr}" if from_addr else target)
                if target and self._is_dangerous_call_target(target):
                    dangerous_ref = (target, from_addr or None)
                    if dangerous_ref not in entry.dangerous_call_refs:
                        entry.dangerous_call_refs.append(dangerous_ref)
                issue = call_site.get("issue")
                if not isinstance(issue, dict):
                    continue
                issue_type = issue.get("type")
                evidence = self._compact_fact_text(issue.get("evidence"))
                if issue_type == "format-string":
                    self._append_unique(
                        entry.issue_lines,
                        f"`function_disasm` 显示 `{entry.name}` 将可控数据直接作为 `printf` 格式串（{evidence or '参数快照已命中格式串模式'}）。",
                    )
                    entry.score += 12
                elif issue_type == "overflow-candidate":
                    self._append_unique(
                        entry.issue_lines,
                        f"`function_disasm` 显示 `{entry.name}` 的输入长度超过缓冲区容量估计（{evidence or '长度参数大于缓冲区容量'}）。",
                    )
                    entry.score += 10

            if isinstance(stack_frame, int):
                self._append_unique(
                    entry.fact_lines,
                    f"`function_disasm` 识别 `{entry.name}` 的栈帧大小约为 `{hex(stack_frame)}`。",
                )
                entry.score += 1
            if interesting_calls:
                self._append_unique(
                    entry.fact_lines,
                    f"`function_disasm` 中可见关键调用链：{', '.join(interesting_calls)}。",
                )
                entry.score += 2

    def _ingest_function_xrefs(
        self,
        entries: dict[str, FunctionReportEntry],
        role: str,
        payload: dict[str, Any],
    ) -> None:
        for item in payload.get("functions", []) or []:
            if not isinstance(item, dict):
                continue
            entry = self._upsert_function_entry(entries, item.get("name"), item.get("address"), role, "function_xrefs")
            callers = item.get("callers") or []
            caller_count = item.get("caller_count")
            if caller_count == 0:
                self._append_unique(
                    entry.caller_lines,
                    f"`function_xrefs` 未发现 `{entry.name}` 的调用者。",
                )
                entry.score += 1
                continue
            caller_preview: list[str] = []
            for caller in callers[:3]:
                if not isinstance(caller, dict):
                    continue
                caller_name = str(caller.get("function") or "unknown")
                caller_addr = str(caller.get("from") or "")
                caller_ref = (caller_name, caller_addr or None)
                if caller_ref not in entry.caller_refs:
                    entry.caller_refs.append(caller_ref)
                caller_preview.append(f"{caller_name}@{caller_addr}" if caller_addr else caller_name)
            if caller_preview:
                self._append_unique(
                    entry.caller_lines,
                    f"`function_xrefs` 记录 `{entry.name}` 的调用者：{', '.join(caller_preview)}。",
                )
                entry.score += 3

    def _ingest_rizin_overview(
        self,
        entries: dict[str, FunctionReportEntry],
        role: str,
        payload: dict[str, Any],
    ) -> None:
        dangerous_xrefs = payload.get("dangerous_xrefs") or {}
        if not isinstance(dangerous_xrefs, dict):
            return
        for symbol, refs in dangerous_xrefs.items():
            if not isinstance(refs, list):
                continue
            for ref in refs[:6]:
                if not isinstance(ref, dict):
                    continue
                function_name = ref.get("function")
                if not isinstance(function_name, str) or not function_name:
                    continue
                entry = self._upsert_function_entry(entries, function_name, None, role, "rizin_overview")
                from_addr = str(ref.get("from") or "")
                dangerous_ref = (str(symbol), from_addr or None)
                if dangerous_ref not in entry.dangerous_call_refs:
                    entry.dangerous_call_refs.append(dangerous_ref)
                self._append_unique(
                    entry.fact_lines,
                    f"`rizin_overview` 记录 `{entry.name}` 在 `{from_addr or 'unknown'}` 调用了危险导入 `{symbol}`。",
                )
                entry.score += 4

    def _ingest_ida_preview(
        self,
        entries: dict[str, FunctionReportEntry],
        role: str,
        payload: dict[str, Any],
    ) -> None:
        for item in payload.get("function_index_preview", []) or []:
            if not isinstance(item, dict):
                continue
            address = item.get("address") or item.get("ea")
            entry = self._upsert_function_entry(entries, item.get("name"), address, role, "ida_batch")
            self._append_unique(
                entry.fact_lines,
                f"`ida_batch` 已恢复 `{entry.name}` 的函数索引。",
            )
            entry.score += 1

    def _ingest_angr_preview(
        self,
        entries: dict[str, FunctionReportEntry],
        role: str,
        payload: dict[str, Any],
    ) -> None:
        for item in payload.get("functions", []) or []:
            if not isinstance(item, dict):
                continue
            entry = self._upsert_function_entry(entries, item.get("name"), item.get("addr"), role, "angr_cfg")
            self._append_unique(
                entry.fact_lines,
                f"`angr_cfg` 已把 `{entry.name}` 纳入 CFG 恢复结果。",
            )
            entry.score += 1

    def _ingest_gdb_poc(
        self,
        entries: dict[str, FunctionReportEntry],
        role: str,
        payload: dict[str, Any],
    ) -> None:
        function = payload.get("function") or {}
        if not isinstance(function, dict):
            return
        entry = self._upsert_function_entry(
            entries,
            function.get("name"),
            function.get("address"),
            role,
            "gdb_poc",
        )
        issue_type = self._compact_fact_text(payload.get("issue_type")) or "unknown"
        assessment = payload.get("rce_assessment") or {}
        if not isinstance(assessment, dict):
            assessment = self._synthesize_rce_assessment_from_poc_payload(payload)
        stage_label = self._compact_fact_text(assessment.get("stage_label"))
        verdict = self._compact_fact_text(assessment.get("verdict"))
        boundary = self._compact_fact_text(assessment.get("boundary"))
        gdb_observation = payload.get("gdb_observation") or {}
        if not isinstance(gdb_observation, dict):
            gdb_observation = {}
        native_probe = payload.get("native_probe") or {}
        if not isinstance(native_probe, dict):
            native_probe = {}

        if stage_label:
            self._append_unique(
                entry.issue_lines,
                f"`gdb_poc` 已把 `{entry.name}` 的 `{issue_type}` 原语推进到“{stage_label}”。",
            )
            entry.score += 14
        if verdict:
            self._append_unique(entry.fact_lines, f"`gdb_poc` 结论：{verdict}")
            entry.score += 4
        if boundary:
            self._append_unique(entry.fact_lines, f"`gdb_poc` 当前边界：{boundary}")
            entry.score += 3

        for label, value in (
            ("GDB 断点命中", gdb_observation.get("breakpoint_line")),
            ("GDB 实参取证", gdb_observation.get("argument_line")),
            ("GDB 崩溃信号", gdb_observation.get("signal_line")),
            ("原生输出", native_probe.get("probe_line") or native_probe.get("stdout_preview")),
        ):
            compact_value = self._compact_fact_text(value)
            if compact_value:
                self._append_unique(entry.fact_lines, f"`gdb_poc` {label}: {compact_value[:220]}")

        control_offset = gdb_observation.get("control_offset")
        if isinstance(control_offset, int):
            self._append_unique(entry.issue_lines, f"`gdb_poc` 已在 RIP 上定位循环模式偏移 `{control_offset}`。")
            entry.score += 6

    def _upsert_function_entry(
        self,
        entries: dict[str, FunctionReportEntry],
        name_value: Any,
        address_value: Any,
        role: str,
        tool_name: str,
    ) -> FunctionReportEntry:
        name = self._canonicalize_function_name(name_value)
        address = self._normalize_address(address_value)
        key = f"{name}@{address or 'na'}"
        entry = entries.get(key)
        fallback_key = f"{name}@na"
        if entry is None and address is not None and fallback_key in entries:
            entry = entries.pop(fallback_key)
            entry.address = address
            entries[key] = entry
        if entry is None and address is None:
            for existing_key, existing_entry in entries.items():
                if existing_entry.name == name and existing_key.startswith(f"{name}@"):
                    entry = existing_entry
                    break
        if entry is None:
            entry = FunctionReportEntry(name=name, address=address)
            entries[key] = entry
        elif entry.address is None and address is not None:
            entry.address = address
        entry.roles.add(role)
        entry.tools.add(tool_name)
        return entry

    def _canonicalize_function_name(self, name_value: Any) -> str:
        raw_name = str(name_value or "unknown").strip() or "unknown"
        for prefix in ("sym.", "fcn.", "dbg.", "imp."):
            if raw_name.startswith(prefix):
                return raw_name[len(prefix):]
        return raw_name

    def _normalize_address(self, address_value: Any) -> str | None:
        if address_value is None:
            return None
        if isinstance(address_value, int):
            return hex(address_value)
        text = str(address_value).strip()
        if not text:
            return None
        return text

    def _build_knowledge_entries(self, *, include_hidden: bool) -> list[KnowledgeEntry]:
        hidden_ids = self.repository.load_hidden_knowledge_entry_ids()
        entries: list[KnowledgeEntry] = []
        for session in self.repository.list_sessions(limit=None):
            if session.status != SessionStatus.COMPLETED:
                continue
            for candidate in self._select_knowledge_candidates_for_session(session):
                entry_id = self._knowledge_entry_id_for_key(session.id, candidate["key"], candidate["text"])
                if not include_hidden and entry_id in hidden_ids:
                    continue
                entries.append(
                    KnowledgeEntry(
                        id=entry_id,
                        session_id=session.id,
                        session_title=session.request.title,
                        role=str(candidate["role"]),
                        text=str(candidate["text"]),
                        created_at=session.updated_at,
                    )
                )
        entries.sort(key=lambda item: item.created_at or utcnow(), reverse=True)
        return entries

    def _knowledge_entry_id(self, session_id: str, task_id: str, index: int, note: str) -> str:
        digest = hashlib.sha1(f"{session_id}:{task_id}:{index}:{note}".encode("utf-8")).hexdigest()[:16]
        return f"{session_id}-{task_id[:8]}-{index}-{digest}"

    def _knowledge_entry_id_for_key(self, session_id: str, key: str, note: str) -> str:
        digest = hashlib.sha1(f"{session_id}:{key}:{note}".encode("utf-8")).hexdigest()[:16]
        return f"{session_id}-{key[:24]}-{digest}"

    def _select_knowledge_candidates_for_session(self, session: AuditSession) -> list[dict[str, str]]:
        candidates: list[dict[str, str]] = []
        seen_texts: set[str] = set()

        flow_note = self._build_session_flow_knowledge_note(session)
        if flow_note:
            candidates.append({"key": "flow", "role": "manager", "text": flow_note})
            seen_texts.add(flow_note)

        for index, item in enumerate(self._build_session_risk_knowledge_notes(session), start=1):
            if item["text"] in seen_texts:
                continue
            seen_texts.add(item["text"])
            candidates.append(
                {
                    "key": f"risk-{index}-{item['role']}",
                    "role": item["role"],
                    "text": item["text"],
                }
            )
            if len(candidates) >= 3:
                break
        return candidates[:3]

    def _build_session_flow_knowledge_note(self, session: AuditSession) -> str:
        roles = [task.role for task in session.subagents if task.role]
        if not roles and not session.manager_plan_summary:
            return ""
        role_flow = " -> ".join(roles[:5]) if roles else "manager-only"
        focus = self._extract_plan_focus_points(session.manager_plan_summary)
        focus_text = f"；重点围绕 {'；'.join(focus[:2])}" if focus else ""
        return f"流程摘要：Manager 按 {role_flow} 推进取证与复核{focus_text}。"

    def _extract_plan_focus_points(self, manager_plan_summary: str | None) -> list[str]:
        if not manager_plan_summary:
            return []
        focus_points: list[str] = []
        capture = False
        for raw_line in manager_plan_summary.splitlines():
            line = raw_line.strip()
            heading = line.lstrip("#").strip()
            if heading == "跨角色重点":
                capture = True
                continue
            if capture and line.startswith("## "):
                break
            if capture and line.startswith("- "):
                focus_points.append(line[2:].strip())
        return focus_points[:4]

    def _build_session_risk_knowledge_notes(self, session: AuditSession) -> list[dict[str, str]]:
        notes: list[dict[str, str]] = []
        seen: set[str] = set()

        for payload in self._collect_rce_payloads(session):
            assessment = payload["assessment"]
            summary = self._compact_fact_text(assessment.get("verdict"))
            if not summary:
                continue
            text = f"危险点：{payload['function_title']} - {payload['stage_label']}；{summary}"
            if text in seen:
                continue
            seen.add(text)
            notes.append(
                {
                    "role": str(payload["task_role"]),
                    "text": text,
                    "score": str(self._rce_stage_rank(payload["stage_id"])),
                }
            )

        for task in session.subagents:
            for note in task.promoted_notes:
                normalized = self._compact_fact_text(note)
                if not normalized or not self._is_knowledge_risk_note(normalized):
                    continue
                text = f"危险点：{normalized}"
                if text in seen:
                    continue
                seen.add(text)
                notes.append(
                    {
                        "role": task.role,
                        "text": text,
                        "score": str(self._knowledge_risk_score(normalized)),
                    }
                )

        notes.sort(key=lambda item: int(item["score"]), reverse=True)
        return notes[:2]

    def _is_knowledge_risk_note(self, text: str) -> bool:
        danger_tokens = (
            "危险点",
            "主漏洞",
            "函数风险",
            "格式化字符串",
            "栈溢出",
            "溢出",
            "信息泄露",
            "RCE",
            "getshell",
            "任意",
            "控制流",
            "RIP",
            "命令执行",
        )
        return any(token in text for token in danger_tokens)

    def _knowledge_risk_score(self, text: str) -> int:
        score = 0
        weights = (
            ("RCE", 12),
            ("getshell", 12),
            ("命令执行", 10),
            ("控制流", 9),
            ("RIP", 9),
            ("任意", 8),
            ("格式化字符串", 7),
            ("栈溢出", 7),
            ("溢出", 6),
            ("信息泄露", 5),
            ("主漏洞", 4),
            ("函数风险", 4),
        )
        for token, value in weights:
            if token in text:
                score += value
        return score

    def _prune_hidden_knowledge_entries_for_session(self, session: AuditSession) -> None:
        hidden_ids = self.repository.load_hidden_knowledge_entry_ids()
        session_entry_ids = {
            self._knowledge_entry_id_for_key(session.id, item["key"], item["text"])
            for item in self._select_knowledge_candidates_for_session(session)
        }
        if not session_entry_ids.intersection(hidden_ids):
            return
        self.repository.save_hidden_knowledge_entry_ids(hidden_ids - session_entry_ids)

    def _artifact_referenced_elsewhere(self, artifact_id: str, *, excluding_session_id: str) -> bool:
        for session in self.repository.list_sessions(limit=None):
            if session.id == excluding_session_id:
                continue
            if session.request.artifact_id == artifact_id:
                return True
        return False

    def _delete_artifact_bundle(self, artifact_id: str) -> None:
        try:
            artifact = self.repository.load_artifact(artifact_id)
        except FileNotFoundError:
            return
        artifact_path = Path(artifact.stored_path)
        artifact_path.unlink(missing_ok=True)
        try:
            artifact_path.parent.rmdir()
        except OSError:
            pass
        self.repository.delete_artifact(artifact_id)

    def _compact_session_for_listing(self, session: AuditSession) -> AuditSession:
        compact = session.model_copy(deep=True)
        compact.core_notes = []
        compact.shared_memory = compact.shared_memory[-4:]
        compact.manager_plan_summary = None
        compact.manager_plan = None
        compact.manager_plan_history = []
        compact.final_report = None
        compact.events = compact.events[-4:]
        for task in compact.subagents:
            task.plan_summary = None
            if task.output_summary:
                task.output_summary = task.output_summary[:320]
            task.interventions = []
            task.events = task.events[-4:]
            task.promoted_notes = task.promoted_notes[:3]
            task.evidence = [
                item.model_copy(
                    update={
                        "command": [item.command_id],
                        "stdout": "",
                        "stderr": "",
                        "metadata": {},
                    }
                )
                for item in task.evidence
            ]
        return compact

    def _cleanup_finished_uploaded_artifact(self, session: AuditSession) -> None:
        artifact_id = session.request.artifact_id
        if not artifact_id:
            return
        if session.status not in {SessionStatus.COMPLETED, SessionStatus.FAILED}:
            return
        if self._artifact_referenced_elsewhere(artifact_id, excluding_session_id=session.id):
            return
        self._delete_artifact_bundle(artifact_id)

    def _mask_api_key(self, api_key: str | None) -> str | None:
        normalized = (api_key or "").strip()
        if not normalized:
            return None
        if len(normalized) <= 8:
            return "*" * len(normalized)
        return f"{normalized[:4]}...{normalized[-4:]}"

    def _apply_settings_patch(self, updates: dict[str, Any]) -> None:
        if not updates:
            return
        candidate_payload = self.settings.model_dump()
        touched_fields = set(updates)
        for field_name, value in updates.items():
            candidate_payload[field_name] = self._normalize_setting_patch_value(value)

        validated = Settings(**candidate_payload)
        ensure_directories(validated)

        for field_name in Settings.model_fields:
            setattr(self.settings, field_name, getattr(validated, field_name))

        for field_name in touched_fields:
            env_key = self._settings_env_key(field_name)
            rendered = self._render_env_setting_value(getattr(validated, field_name))
            self._persist_env_value(env_key, rendered)

        self.router = ModelRouter(self.settings)
        self.llm_backend = create_llm_backend(self.settings)
        self.pwn_skill = PwnSkillPack(self.settings)
        self._refresh_tool_runtime()

    def _normalize_setting_patch_value(self, value: Any) -> Any:
        if isinstance(value, str):
            normalized = value.strip()
            return normalized or None
        return value

    def _settings_env_key(self, field_name: str) -> str:
        field = Settings.model_fields.get(field_name)
        return str(field.alias or field_name).upper()

    def _render_env_setting_value(self, value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, Path):
            return str(value)
        return str(value)

    def _persist_env_value(self, key: str, value: str | None) -> None:
        env_path = self.settings.env_file_path
        pattern = re.compile(rf"^\s*(?:export\s+)?{re.escape(key)}\s*=")
        lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []
        rendered_value = None
        if value is not None:
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            rendered_value = f'{key}="{escaped}"'

        updated_lines: list[str] = []
        replaced = False
        for line in lines:
            if pattern.match(line):
                if rendered_value is not None:
                    updated_lines.append(rendered_value)
                replaced = True
                continue
            updated_lines.append(line)
        if not replaced and rendered_value is not None:
            updated_lines.append(rendered_value)
        env_path.write_text(
            ("\n".join(updated_lines).rstrip() + "\n") if updated_lines else "",
            encoding="utf-8",
        )

    def _render_tool_digest(self, evidence: list) -> str:
        completed = [item.command_id for item in evidence if item.status == "completed"]
        limited = [f"{item.command_id}={item.status}" for item in evidence if item.status != "completed"]
        parts: list[str] = []
        if completed:
            parts.append("已完成: " + ", ".join(completed[:8]))
        if limited:
            parts.append("受限: " + ", ".join(limited[:6]))
        return "；".join(parts) or "无证据"

    def _extract_summary_key_points(self, summary: str | None, *, limit: int) -> list[str]:
        sanitized = self._sanitize_subagent_summary(summary)
        if not sanitized:
            return []
        points: list[str] = []
        for raw_line in sanitized.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("- "):
                candidate = line[2:].strip()
            else:
                match = re.match(r"^\d+\.\s+(.*)$", line)
                if not match:
                    continue
                candidate = match.group(1).strip()
            if candidate in {"已验证发现", "关键函数深度分析", "利用性判断", "值得提升为核心笔记的结论"}:
                continue
            if candidate not in points:
                points.append(candidate)
            if len(points) >= limit:
                break
        return points

    def _select_task_key_points(
        self,
        task: SubAgentTask,
        manager_highlights: list[str],
        *,
        limit: int,
    ) -> list[str]:
        format_string_refuted = any(
            "排除格式化字符串" in item or ("误报" in item and "printf" in item and "puts" in item)
            for item in manager_highlights
        )
        candidates = task.promoted_notes or self._extract_summary_key_points(task.output_summary, limit=6)
        selected: list[str] = []
        for item in candidates:
            if self._is_incomplete_report_line(item):
                continue
            if format_string_refuted and ("格式化字符串" in item or "格式串" in item or "%n" in item):
                continue
            if item not in selected:
                selected.append(item)
            if len(selected) >= limit:
                break
        return selected

    def _load_json_payload(self, text: str) -> Any:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None

    def _compact_fact_text(self, value: Any) -> str:
        if value is None:
            return ""
        return re.sub(r"\s+", " ", str(value)).strip()

    def _append_unique(self, bucket: list[str], value: str) -> None:
        cleaned = value.strip()
        if cleaned and cleaned not in bucket:
            bucket.append(cleaned)

    def _find_function_entry(
        self,
        entries: dict[str, FunctionReportEntry],
        function_name: str,
    ) -> FunctionReportEntry | None:
        for entry in entries.values():
            if entry.name == function_name:
                return entry
        return None

    def _is_incomplete_report_line(self, text: str) -> bool:
        normalized = text.strip()
        if any(token in normalized for token in self.INCOMPLETE_TOKENS):
            return True
        if normalized.startswith(("若", "如果", "否则若", "如若")):
            return True
        if re.search(r"(?:^|[：:，,（(])(?:若|如果|否则若|如若)", normalized):
            return True
        return normalized.startswith(("使用 ", "提供 ", "补充 ", "验证 ", "获取 ", "必要时", "如需"))

    def _report_markdown(self, session: AuditSession) -> str:
        return session.final_report or self._compose_final_report(session)

    def _refresh_session_report(self, session: AuditSession) -> AuditSession:
        if not session.subagents:
            return session
        if session.status not in {SessionStatus.COMPLETED, SessionStatus.FAILED} and not session.final_report:
            return session
        composed = self._compose_final_report(session)
        if session.final_report != composed:
            session.final_report = composed
            self.repository.save_session(session)
        return session

    async def _record_subagent_event(self, session_id: str, task_id: str, event: AuditEvent) -> None:
        publish_snapshot = event.kind in {
            EventKind.INTERVENTION_INJECTED,
            EventKind.CONTEXT_RESET,
            EventKind.LLM_USAGE_RECORDED,
            EventKind.SUBAGENT_COMPLETED,
        }

        async with self._session_lock(session_id):
            try:
                session = self.repository.load_session(session_id)
            except FileNotFoundError:
                return
            for task in session.subagents:
                if task.id != task_id:
                    continue
                if event.kind == EventKind.LLM_USAGE_RECORDED:
                    self._apply_usage_payload(task.token_usage, event.payload)
                task.events.append(event)
                break
            if event.kind == EventKind.LLM_USAGE_RECORDED:
                self._recompute_session_token_usage(session)
            self.repository.save_session(session)

        await self.broker.publish_event(session_id, event, task_id=task_id)
        if publish_snapshot:
            await self.broker.publish_snapshot(session)

    async def _persist_subagent_result(self, session_id: str, result) -> None:
        async with self._session_lock(session_id):
            try:
                session = self.repository.load_session(session_id)
            except FileNotFoundError:
                return
            for task in session.subagents:
                if task.id != result.task_id:
                    continue
                sanitized_summary = self._sanitize_subagent_summary(result.summary)
                task.status = result.status
                task.plan_summary = result.plan_summary
                task.output_summary = sanitized_summary
                task.token_usage = result.token_usage
                task.evidence = result.evidence
                task.interventions = result.interventions
                task.promoted_notes = result.promoted_notes
                task.events = result.events
                task.container_id = result.container_id
                task.finished_at = utcnow()
                task.error = result.error
                break
            self._recompute_session_token_usage(session)
            self.repository.save_session(session)
        await self.broker.publish_snapshot(session)

    def _session_lock(self, session_id: str) -> asyncio.Lock:
        if session_id not in self.session_locks:
            self.session_locks[session_id] = asyncio.Lock()
        return self.session_locks[session_id]

    def _sanitize_subagent_summary(self, summary: str | None) -> str | None:
        if summary is None:
            return None

        blocked_tokens = (
            "下一步",
            "后续",
            "建议",
            "需进一步",
            "可继续",
            "继续分析",
            *self.INCOMPLETE_TOKENS,
        )
        sanitized_lines: list[str] = []
        for raw_line in summary.splitlines():
            line = raw_line.strip()
            normalized = line.lstrip("#").strip()
            if not line:
                if sanitized_lines and sanitized_lines[-1] != "":
                    sanitized_lines.append("")
                continue
            if any(token in normalized for token in blocked_tokens) or self._is_incomplete_report_line(normalized):
                continue
            sanitized_lines.append(raw_line)

        while sanitized_lines and sanitized_lines[-1] == "":
            sanitized_lines.pop()
        return "\n".join(sanitized_lines).strip()
