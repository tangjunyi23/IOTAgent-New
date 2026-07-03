from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DifficultyHint(StrEnum):
    AUTO = "auto"
    ROUTINE = "routine"
    HARD = "hard"


class SessionStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class SubAgentStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ReportExportFormat(StrEnum):
    MARKDOWN = "markdown"
    JSON = "json"


class EventKind(StrEnum):
    ARTIFACT_UPLOADED = "artifact_uploaded"
    SESSION_CREATED = "session_created"
    SESSION_STARTED = "session_started"
    SUBAGENT_STARTED = "subagent_started"
    AGENT_MESSAGE_SENT = "agent_message_sent"
    AGENT_MESSAGE_RECEIVED = "agent_message_received"
    REASONING_ROUND = "reasoning_round"
    NOTE_RETRIEVAL = "note_retrieval"
    TOOL_INVOCATION = "tool_invocation"
    TOOL_RESULT = "tool_result"
    LLM_USAGE_RECORDED = "llm_usage_recorded"
    INTERVENTION_INJECTED = "intervention_injected"
    NOTE_EVICTED = "note_evicted"
    CONTEXT_RESET = "context_reset"
    SUBAGENT_COMPLETED = "subagent_completed"
    SESSION_COMPLETED = "session_completed"
    SESSION_FAILED = "session_failed"


class AuditEvent(BaseModel):
    kind: EventKind
    message: str
    created_at: datetime = Field(default_factory=utcnow)
    agent_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class NoteEntry(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    content: str
    source: str
    is_core: bool = False
    retrieval_count: int = 0
    invalidated: bool = False
    created_at: datetime = Field(default_factory=utcnow)
    last_retrieved_at: datetime | None = None


class SharedMemoryEntry(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    content: str
    source: str
    category: str = "fact"
    round_index: int | None = None
    role: str | None = None
    priority: int = 0
    created_at: datetime = Field(default_factory=utcnow)


class TokenUsageSnapshot(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    reasoning_tokens: int = 0
    cached_tokens: int = 0
    llm_calls: int = 0


class Intervention(BaseModel):
    source: str
    instruction: str
    created_at: datetime = Field(default_factory=utcnow)


class AgentMessage(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    session_id: str
    sender_task_id: str
    sender_role: str
    stage: str
    message_kind: str = "update"
    topic: str | None = None
    recipients: list[str] = Field(default_factory=list)
    requires_response: bool = False
    in_reply_to: str | None = None
    content: str
    created_at: datetime = Field(default_factory=utcnow)


class CommandEvidence(BaseModel):
    command_id: str
    command: list[str]
    return_code: int
    tool_name: str | None = None
    status: str = "completed"
    stdout: str = ""
    stderr: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)


class ToolCapability(BaseModel):
    tool_id: str
    family: str
    available: bool
    enabled: bool = True
    executable: str | None = None
    mode: str
    summary: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ToolHealthCheckResult(BaseModel):
    tool_id: str
    available: bool
    enabled: bool
    status: str
    summary: str
    details: str | None = None
    executable: str | None = None
    checked_at: datetime = Field(default_factory=utcnow)


class ArtifactRecord(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    filename: str
    stored_path: str
    sha256: str
    size_bytes: int
    created_at: datetime = Field(default_factory=utcnow)


class KnowledgeEntry(BaseModel):
    id: str
    session_id: str
    session_title: str
    role: str
    text: str
    created_at: datetime | None = None


class ManagerPlanRole(BaseModel):
    role: str
    objective: str
    coordination_focus: list[str] = Field(default_factory=list)
    collaboration_targets: list[str] = Field(default_factory=list)
    expected_evidence: list[str] = Field(default_factory=list)
    planned_steps: list[str] = Field(default_factory=list)
    stage_goal: str | None = None
    priority: int = 100


class ManagerPlanPhase(BaseModel):
    phase: str
    goal: str
    owner_roles: list[str] = Field(default_factory=list)
    exit_criteria: list[str] = Field(default_factory=list)


class ManagerPlanOutline(BaseModel):
    strategy_summary: str = ""
    global_focus: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)
    phase_plan: list[ManagerPlanPhase] = Field(default_factory=list)
    risk_watchpoints: list[str] = Field(default_factory=list)
    roles: list[ManagerPlanRole] = Field(default_factory=list)


class AuditRequest(BaseModel):
    title: str
    objective: str
    artifact_id: str | None = None
    target_path: str | None = None
    difficulty: DifficultyHint = DifficultyHint.AUTO
    max_subagents: int = 3
    desired_outcome: str | None = None
    audit_mode: str | None = None
    analyst_notes: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_target(self) -> "AuditRequest":
        if not self.artifact_id and not self.target_path:
            raise ValueError("artifact_id or target_path is required")
        return self


class SubAgentTask(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    role: str
    objective: str
    model: str
    planning_model: str | None = None
    discussion_model: str | None = None
    summary_model: str | None = None
    round_index: int = 1
    status: SubAgentStatus = SubAgentStatus.QUEUED
    target_path: str
    evidence: list[CommandEvidence] = Field(default_factory=list)
    output_summary: str | None = None
    plan_summary: str | None = None
    coordination_focus: list[str] = Field(default_factory=list)
    collaboration_targets: list[str] = Field(default_factory=list)
    expected_evidence: list[str] = Field(default_factory=list)
    planned_steps: list[str] = Field(default_factory=list)
    manager_step_total: int = 0
    manager_step_completed: int = 0
    manager_completion_confirmed: bool = False
    manager_review_summary: str | None = None
    stage_goal: str | None = None
    continuation_brief: list[str] = Field(default_factory=list)
    reused_tool_ids: list[str] = Field(default_factory=list)
    token_usage: TokenUsageSnapshot = Field(default_factory=TokenUsageSnapshot)
    interventions: list[Intervention] = Field(default_factory=list)
    promoted_notes: list[str] = Field(default_factory=list)
    events: list[AuditEvent] = Field(default_factory=list)
    container_id: str | None = None
    error: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


class SubAgentPayload(BaseModel):
    session_id: str
    session_title: str
    task: SubAgentTask
    core_notes: list[NoteEntry]
    shared_memory: list[SharedMemoryEntry] = Field(default_factory=list)
    seed_evidence: list[CommandEvidence] = Field(default_factory=list)
    available_tool_ids: list[str] = Field(default_factory=list)
    objective: str
    target_path: str
    manager_plan_summary: str | None = None
    event_stream_path: str | None = None
    coordination_dir: str | None = None
    peer_count: int = 0
    peer_roles: list[str] = Field(default_factory=list)
    # When True, the subagent worker continues this role's existing conversation
    # state (messages history) from a prior round instead of starting fresh.
    # Keyed by (session_id, role). Docker runtime does not persist in-process
    # state — see Phase D for file-based persistence.
    continue_role_session: bool = False


class SubAgentResult(BaseModel):
    task_id: str
    status: SubAgentStatus
    plan_summary: str | None = None
    summary: str | None = None
    token_usage: TokenUsageSnapshot = Field(default_factory=TokenUsageSnapshot)
    evidence: list[CommandEvidence] = Field(default_factory=list)
    interventions: list[Intervention] = Field(default_factory=list)
    promoted_notes: list[str] = Field(default_factory=list)
    events: list[AuditEvent] = Field(default_factory=list)
    container_id: str | None = None
    error: str | None = None


class ExportedSubAgentReport(BaseModel):
    task_id: str
    role: str
    model: str
    status: SubAgentStatus
    token_usage: TokenUsageSnapshot = Field(default_factory=TokenUsageSnapshot)
    summary: str | None = None
    plan_summary: str | None = None
    promoted_notes: list[str] = Field(default_factory=list)
    evidence: list[CommandEvidence] = Field(default_factory=list)
    interventions: list[Intervention] = Field(default_factory=list)
    error: str | None = None


class AuditReportExport(BaseModel):
    session_id: str
    title: str
    status: SessionStatus
    target_path: str | None = None
    objective: str
    desired_outcome: str | None = None
    audit_mode: str | None = None
    difficulty: DifficultyHint
    tags: list[str] = Field(default_factory=list)
    core_notes: list[str] = Field(default_factory=list)
    report_markdown: str
    subagents: list[ExportedSubAgentReport] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=utcnow)


class LLMProviderSettingsView(BaseModel):
    configured: bool
    key_preview: str | None = None
    base_url: str
    provider: str = "openai-compatible"
    status: str


class LLMProviderSettingsUpdate(BaseModel):
    api_key: str | None = None
    base_url: str | None = None


class LLMProviderCheckRequest(BaseModel):
    api_key: str | None = None
    base_url: str | None = None
    model: str | None = None


class LLMModelInfo(BaseModel):
    id: str
    owned_by: str | None = None


class LLMProviderModelsResult(BaseModel):
    available: bool
    provider: str = "openai-compatible"
    base_url: str
    models: list[LLMModelInfo] = Field(default_factory=list)
    status: str
    error: str | None = None
    checked_at: datetime = Field(default_factory=utcnow)


class LLMProviderCheckResult(BaseModel):
    available: bool
    provider: str = "openai-compatible"
    model: str
    base_url: str
    status: str
    error: str | None = None
    checked_at: datetime = Field(default_factory=utcnow)


class SystemSettingsView(BaseModel):
    llm_provider: str = "openai-compatible"
    llm_configured: bool
    llm_key_preview: str | None = None
    llm_status: str
    llm_base_url: str
    deepseek_configured: bool | None = None
    deepseek_key_preview: str | None = None
    deepseek_status: str | None = None
    deepseek_base_url: str | None = None
    manager_regular_model: str | None = None
    manager_hard_model: str | None = None
    upload_dir: str
    audit_dir: str
    artifact_meta_dir: str
    runtime_dir: str
    skill_data_dir: str
    knowledge_deleted_path: str
    enable_docker_runtime: bool
    subagent_docker_image: str
    subagent_docker_network_mode: str
    host_workspace_dir: str
    max_parallel_subagents: int
    loop_threshold: int
    note_recall_threshold: int
    round_reset_threshold: int
    agent_discussion_max_rounds: int
    agent_coordination_timeout_seconds: float
    llm_timeout_seconds: int
    tool_output_limit: int
    tool_timeout_seconds: int
    ida_headless_path: str | None = None
    host_ida_install_dir: str | None = None
    host_ida_user_dir: str | None = None
    rootfs_elf_tool_dir: str | None = None


class SystemSettingsUpdate(BaseModel):
    llm_base_url: str | None = None
    deepseek_base_url: str | None = None
    manager_regular_model: str | None = None
    manager_hard_model: str | None = None
    upload_dir: str | None = None
    audit_dir: str | None = None
    artifact_meta_dir: str | None = None
    runtime_dir: str | None = None
    skill_data_dir: str | None = None
    knowledge_deleted_path: str | None = None
    enable_docker_runtime: bool | None = None
    subagent_docker_image: str | None = None
    subagent_docker_network_mode: str | None = None
    host_workspace_dir: str | None = None
    max_parallel_subagents: int | None = None
    loop_threshold: int | None = None
    note_recall_threshold: int | None = None
    round_reset_threshold: int | None = None
    agent_discussion_max_rounds: int | None = None
    agent_coordination_timeout_seconds: float | None = None
    llm_timeout_seconds: int | None = None
    tool_output_limit: int | None = None
    tool_timeout_seconds: int | None = None
    ida_headless_path: str | None = None
    host_ida_install_dir: str | None = None
    host_ida_user_dir: str | None = None
    rootfs_elf_tool_dir: str | None = None


class ToolToggleUpdate(BaseModel):
    enabled: bool


class AuditSession(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    request: AuditRequest
    status: SessionStatus = SessionStatus.QUEUED
    manager_round: int = 0
    core_notes: list[NoteEntry] = Field(default_factory=list)
    shared_memory: list[SharedMemoryEntry] = Field(default_factory=list)
    manager_plan_summary: str | None = None
    manager_plan: ManagerPlanOutline | None = None
    manager_plan_history: list[ManagerPlanOutline] = Field(default_factory=list)
    manager_token_usage: TokenUsageSnapshot = Field(default_factory=TokenUsageSnapshot)
    token_usage: TokenUsageSnapshot = Field(default_factory=TokenUsageSnapshot)
    subagents: list[SubAgentTask] = Field(default_factory=list)
    events: list[AuditEvent] = Field(default_factory=list)
    final_report: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    def touch(self) -> None:
        self.updated_at = utcnow()
