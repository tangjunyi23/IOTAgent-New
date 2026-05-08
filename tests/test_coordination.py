import asyncio
import json
from pathlib import Path

import pytest

from app.config import ROOT_DIR, Settings, ensure_directories
from app.coordination import AgentMailbox
from app.models import CommandEvidence, EventKind, SubAgentPayload, SubAgentResult, SubAgentStatus, SubAgentTask
from app.subagent import DockerSubAgentRuntime, SubAgentWorker
from app.toolbox import FollowUpRequest


class FakeReply:
    def __init__(self, content: str) -> None:
        self.content = content


class FakeLLMBackend:
    async def plan_session(self, *, request, core_notes, available_tools, selection):
        return FakeReply(
            json.dumps(
                {
                    "strategy_summary": "测试用 Manager 分工。",
                    "roles": [
                        {
                            "role": "triage",
                            "objective": "先做样本属性和危险调用研判。",
                            "coordination_focus": ["main@0x401000"],
                            "collaboration_targets": ["static-analysis"],
                            "priority": 1,
                        },
                        {
                            "role": "static-analysis",
                            "objective": "验证 triage 提到的关键函数。",
                            "coordination_focus": ["main@0x401000"],
                            "collaboration_targets": ["triage"],
                            "priority": 2,
                        },
                    ],
                },
                ensure_ascii=False,
            )
        )

    async def draft_plan(self, *, task, core_notes, selection, interventions):
        return FakeReply(f"计划: {task.role} 先做本地证据采样。")

    async def draft_collaboration(
        self,
        *,
        task,
        core_notes,
        evidence,
        peer_messages,
        selection,
        interventions,
        manager_plan_summary,
        phase_label,
    ):
        return FakeReply(
            "\n".join(
                [
                    "1. 当前已确认",
                    f"- {task.role} 在 {phase_label} 已共享进展。",
                    "2. 希望同伴协查",
                    "- 请回传你们看到的关键函数与调用点。",
                    "3. 当前阻塞",
                    "- 无",
                ]
            )
        )

    async def finalize_analysis(self, *, task, core_notes, evidence, plan, selection, interventions):
        peer_notes = [item for item in core_notes if item.startswith("[来自")]
        return FakeReply(
            "\n".join(
                [
                    "## 4. 值得提升为核心笔记的结论",
                    f"1. peer_seen={len(peer_notes)}",
                    f"2. 角色={task.role}",
                ]
            )
        )


def build_settings(tmp_path: Path) -> Settings:
    settings = Settings(
        data_dir=tmp_path / "data",
        upload_dir=tmp_path / "data" / "uploads",
        audit_dir=tmp_path / "data" / "audits",
        artifact_meta_dir=tmp_path / "data" / "artifacts",
        runtime_dir=tmp_path / "data" / "runtime",
        frontend_dir=ROOT_DIR / "frontend",
        progress_log_path=tmp_path / "docs" / "PROGRESS.md",
        host_workspace_dir=tmp_path,
        deepseek_api_key=None,
        agent_coordination_timeout_seconds=0.6,
        ida_headless_path=tmp_path / "ida-pro" / "idat",
        host_ida_install_dir=tmp_path / "ida-pro",
        host_ida_user_dir=tmp_path / ".idapro",
    )
    ensure_directories(settings)
    settings.host_ida_install_dir.mkdir(parents=True, exist_ok=True)
    settings.ida_headless_path.write_text("", encoding="utf-8")
    settings.ida_headless_path.chmod(0o755)
    assert settings.host_ida_user_dir is not None
    settings.host_ida_user_dir.mkdir(parents=True, exist_ok=True)
    (settings.host_ida_user_dir / "ida.reg").write_text("accepted=1\n", encoding="utf-8")
    settings.progress_log_path.write_text("test progress\n", encoding="utf-8")
    return settings


def test_agent_mailbox_publishes_and_drains_messages(tmp_path: Path):
    mailbox = AgentMailbox(tmp_path / "coordination")
    seen: set[str] = set()

    message = mailbox.publish(
        session_id="s1",
        sender_task_id="task-a",
        sender_role="triage",
        stage="plan",
        content="triage 计划摘要",
    )
    drained = mailbox.drain_for_peer(recipient_task_id="task-b", recipient_role="static-analysis", seen_message_ids=seen)
    assert [item.id for item in drained] == [message.id]
    assert drained[0].sender_role == "triage"
    assert mailbox.drain_for_peer(
        recipient_task_id="task-b",
        recipient_role="static-analysis",
        seen_message_ids=seen,
    ) == []

    targeted = mailbox.publish(
        session_id="s1",
        sender_task_id="task-a",
        sender_role="triage",
        stage="discussion",
        message_kind="question",
        topic="main@0x401000",
        recipients=["exploit-strategy"],
        requires_response=True,
        content="请确认 main 的调用关系。",
    )
    assert mailbox.drain_for_peer(
        recipient_task_id="task-c",
        recipient_role="static-analysis",
        seen_message_ids={message.id},
    ) == []
    filtered = mailbox.drain_for_peer(
        recipient_task_id="task-d",
        recipient_role="exploit-strategy",
        seen_message_ids={message.id},
    )
    assert [item.id for item in filtered] == [targeted.id]


def test_prepare_ida_user_dir_ignores_dangling_symlinks(tmp_path: Path):
    settings = build_settings(tmp_path)
    assert settings.host_ida_user_dir is not None
    plugins_dir = settings.host_ida_user_dir / "plugins"
    plugins_dir.mkdir(parents=True, exist_ok=True)
    (plugins_dir / "broken.py").symlink_to(tmp_path / "missing-plugin.py")

    runtime = DockerSubAgentRuntime(settings)
    staged = runtime._prepare_ida_user_dir(tmp_path / "runtime-task")

    assert staged is not None
    assert (staged / "ida.reg").exists()
    assert not (staged / "plugins" / "broken.py").exists()


def test_prepare_container_target_promotes_workspace_elf_to_executable(tmp_path: Path):
    settings = build_settings(tmp_path)
    sample = settings.upload_dir / "artifact-1" / "pwn"
    sample.parent.mkdir(parents=True, exist_ok=True)
    sample.write_bytes(b"\x7fELFworkspace-sample")
    sample.chmod(0o664)

    runtime = DockerSubAgentRuntime(settings)
    container_path = runtime._prepare_container_target(str(sample), tmp_path / "runtime-task")

    assert container_path == "/workspace/data/uploads/artifact-1/pwn"
    assert sample.stat().st_mode & 0o111


@pytest.mark.asyncio
async def test_subagents_exchange_messages_via_shared_coordination_dir(tmp_path: Path):
    settings = build_settings(tmp_path)
    sample = tmp_path / "sample.bin"
    sample.write_bytes(b"\x7fELFcoordination")
    coordination_dir = tmp_path / "coordination"

    worker_a = SubAgentWorker(settings, llm_backend=FakeLLMBackend())
    worker_b = SubAgentWorker(settings, llm_backend=FakeLLMBackend())

    async def fake_collect(role, target_path, publish):
        return [
            CommandEvidence(
                command_id="file",
                command=["file", target_path],
                return_code=0,
                stdout=f"{target_path}: ELF {role}\n",
            )
        ]

    async def fake_collect_follow_up(target_path, requests, publish):
        return []

    worker_a.toolbox.collect = fake_collect  # type: ignore[method-assign]
    worker_b.toolbox.collect = fake_collect  # type: ignore[method-assign]
    worker_a.toolbox.collect_follow_up = fake_collect_follow_up  # type: ignore[method-assign]
    worker_b.toolbox.collect_follow_up = fake_collect_follow_up  # type: ignore[method-assign]
    worker_a.toolbox.plan_follow_up = lambda role, evidence, round_index, peer_notes=None: []  # type: ignore[method-assign]
    worker_b.toolbox.plan_follow_up = lambda role, evidence, round_index, peer_notes=None: []  # type: ignore[method-assign]

    payload_a = SubAgentPayload(
        session_id="session-1",
        session_title="coordination",
        task=SubAgentTask(role="triage", objective="triage", model="deepseek-v4-flash", target_path=str(sample)),
        core_notes=[],
        objective="验证 agent 间通信",
        target_path=str(sample),
        coordination_dir=str(coordination_dir),
        peer_count=1,
    )
    payload_b = SubAgentPayload(
        session_id="session-1",
        session_title="coordination",
        task=SubAgentTask(role="static-analysis", objective="static", model="deepseek-v4-flash", target_path=str(sample)),
        core_notes=[],
        objective="验证 agent 间通信",
        target_path=str(sample),
        coordination_dir=str(coordination_dir),
        peer_count=1,
    )

    result_a, result_b = await asyncio.gather(
        worker_a.execute(payload_a),
        worker_b.execute(payload_b),
    )

    assert result_a.status == SubAgentStatus.COMPLETED
    assert result_b.status == SubAgentStatus.COMPLETED
    assert "peer_seen=" in (result_a.summary or "")
    assert "peer_seen=" in (result_b.summary or "")
    assert "peer_seen=0" not in (result_a.summary or "")
    assert "peer_seen=0" not in (result_b.summary or "")
    sent_a = [event for event in result_a.events if event.kind == EventKind.AGENT_MESSAGE_SENT]
    recv_a = [event for event in result_a.events if event.kind == EventKind.AGENT_MESSAGE_RECEIVED]
    recv_b = [event for event in result_b.events if event.kind == EventKind.AGENT_MESSAGE_RECEIVED]
    assert len(sent_a) >= 3
    assert len(recv_a) >= 1
    assert len(recv_b) >= 1
    assert any(event.payload.get("message_kind") == "plan" for event in sent_a)
    assert any(event.payload.get("message_kind") == "update" for event in sent_a)


@pytest.mark.asyncio
async def test_subagent_collaboration_cycles_reach_third_follow_up_round(tmp_path: Path):
    settings = build_settings(tmp_path)
    sample = tmp_path / "sample.bin"
    sample.write_bytes(b"\x7fELFcoordination-rounds")

    worker = SubAgentWorker(settings, llm_backend=FakeLLMBackend())
    requested_rounds: list[int] = []

    async def fake_collect(role, target_path, publish):
        return [
            CommandEvidence(
                command_id="file",
                command=["file", target_path],
                return_code=0,
                stdout=f"{target_path}: ELF {role}\n",
            )
        ]

    def fake_plan_follow_up(role, evidence, round_index, peer_notes=None):
        if round_index > 2:
            return []
        requested_rounds.append(round_index)
        return [
            FollowUpRequest(
                command_id=f"round_{round_index}",
                tool_name="internal",
                summary=f"round {round_index}",
                payload={"round": round_index},
            )
        ]

    async def fake_collect_follow_up(target_path, requests, publish):
        return [
            CommandEvidence(
                command_id=request.command_id,
                command=["internal", str(request.payload["round"])],
                return_code=0,
                stdout=f"round={request.payload['round']}",
            )
            for request in requests
        ]

    worker.toolbox.collect = fake_collect  # type: ignore[method-assign]
    worker.toolbox.plan_follow_up = fake_plan_follow_up  # type: ignore[method-assign]
    worker.toolbox.collect_follow_up = fake_collect_follow_up  # type: ignore[method-assign]

    payload = SubAgentPayload(
        session_id="session-rounds",
        session_title="coordination-rounds",
        task=SubAgentTask(role="triage", objective="triage", model="deepseek-v4-flash", target_path=str(sample)),
        core_notes=[],
        objective="验证多轮 follow-up 不会在第 3 轮前被截断",
        target_path=str(sample),
        coordination_dir=str(tmp_path / "coordination-rounds"),
        peer_count=0,
    )

    result = await worker.execute(payload)

    assert result.status == SubAgentStatus.COMPLETED
    assert requested_rounds == [0, 1, 2]
    assert any(item.command_id == "round_0" for item in result.evidence)
    assert any(item.command_id == "round_1" for item in result.evidence)
    assert any(item.command_id == "round_2" for item in result.evidence)


@pytest.mark.asyncio
async def test_completed_static_agent_stays_on_standby_and_can_help_late_peer_request(tmp_path: Path):
    settings = build_settings(tmp_path)
    sample = tmp_path / "standby.bin"
    sample.write_bytes(b"\x7fELFstandby")
    coordination_dir = tmp_path / "coordination-standby"

    worker_static = SubAgentWorker(settings, llm_backend=FakeLLMBackend())
    worker_dynamic = SubAgentWorker(settings, llm_backend=FakeLLMBackend())
    static_summary_sent = asyncio.Event()
    dynamic_question_sent = False

    original_static_publish = worker_static._publish_peer_message

    async def wrapped_static_publish(**kwargs):
        result = await original_static_publish(**kwargs)
        if kwargs.get("stage") == "summary" and kwargs.get("message_kind") == "summary":
            static_summary_sent.set()
        return result

    worker_static._publish_peer_message = wrapped_static_publish  # type: ignore[method-assign]

    async def static_collect(role, target_path, publish):
        return [
            CommandEvidence(
                command_id="file",
                command=["file", target_path],
                return_code=0,
                stdout=f"{target_path}: ELF {role}\n",
            )
        ]

    async def dynamic_collect(role, target_path, publish):
        await asyncio.wait_for(static_summary_sent.wait(), timeout=2.0)
        return [
            CommandEvidence(
                command_id="file",
                command=["file", target_path],
                return_code=0,
                stdout=f"{target_path}: ELF {role}\n",
            )
        ]

    async def static_collect_follow_up(target_path, requests, publish):
        return [
            CommandEvidence(
                command_id=request.command_id,
                command=["internal", request.command_id],
                return_code=0,
                stdout="standby-helped",
            )
            for request in requests
        ]

    async def dynamic_collect_follow_up(target_path, requests, publish):
        return []

    def static_plan_follow_up(role, evidence, round_index, peer_notes=None):
        if any(item.command_id == "standby_static_assist" for item in evidence):
            return []
        if peer_notes and any("main@0x401000" in note for note in peer_notes):
            return [
                FollowUpRequest(
                    command_id="standby_static_assist",
                    tool_name="internal",
                    summary="late static assist",
                    payload={"reason": "peer-question"},
                )
            ]
        return []

    def dynamic_plan_follow_up(role, evidence, round_index, peer_notes=None):
        return []

    def dynamic_blocker_message(payload, evidence, state):
        nonlocal dynamic_question_sent
        if dynamic_question_sent:
            return None
        dynamic_question_sent = True
        return {
            "topic": "main@0x401000",
            "recipients": ["static-analysis"],
            "content": "请静态代理补 main@0x401000 的函数级调用关系。",
        }

    worker_static.toolbox.collect = static_collect  # type: ignore[method-assign]
    worker_dynamic.toolbox.collect = dynamic_collect  # type: ignore[method-assign]
    worker_static.toolbox.collect_follow_up = static_collect_follow_up  # type: ignore[method-assign]
    worker_dynamic.toolbox.collect_follow_up = dynamic_collect_follow_up  # type: ignore[method-assign]
    worker_static.toolbox.plan_follow_up = static_plan_follow_up  # type: ignore[method-assign]
    worker_dynamic.toolbox.plan_follow_up = dynamic_plan_follow_up  # type: ignore[method-assign]
    worker_dynamic._build_blocker_coordination_message = dynamic_blocker_message  # type: ignore[method-assign]

    static_payload = SubAgentPayload(
        session_id="session-standby",
        session_title="coordination-standby",
        task=SubAgentTask(role="static-analysis", objective="static", model="deepseek-v4-flash", target_path=str(sample)),
        core_notes=[],
        objective="验证完成后的静态代理仍可待命支援",
        target_path=str(sample),
        coordination_dir=str(coordination_dir),
        peer_count=1,
        peer_roles=["dynamic-analysis"],
    )
    dynamic_payload = SubAgentPayload(
        session_id="session-standby",
        session_title="coordination-standby",
        task=SubAgentTask(role="dynamic-analysis", objective="dynamic", model="deepseek-v4-pro", target_path=str(sample)),
        core_notes=[],
        objective="验证动态代理可在较晚阶段向静态代理求助",
        target_path=str(sample),
        coordination_dir=str(coordination_dir),
        peer_count=1,
        peer_roles=["static-analysis"],
    )

    static_result, dynamic_result = await asyncio.gather(
        worker_static.execute(static_payload),
        worker_dynamic.execute(dynamic_payload),
    )

    assert static_result.status == SubAgentStatus.COMPLETED
    assert dynamic_result.status == SubAgentStatus.COMPLETED
    assert any(item.command_id == "standby_static_assist" for item in static_result.evidence)
    assert any(
        event.kind == EventKind.AGENT_MESSAGE_RECEIVED and event.payload.get("message_kind") == "question"
        for event in static_result.events
    )
    assert any(
        event.kind == EventKind.AGENT_MESSAGE_SENT and event.payload.get("message_kind") == "answer"
        for event in static_result.events
    )


@pytest.mark.asyncio
async def test_docker_runtime_mounts_coordination_dir_and_reads_cidfile(tmp_path: Path, monkeypatch):
    settings = build_settings(tmp_path)
    settings.subagent_docker_image = "binary-audit-subagent:test"
    runtime = DockerSubAgentRuntime(settings)
    sample = tmp_path / "sample.bin"
    sample.write_bytes(b"\x7fELFdocker")

    payload = SubAgentPayload(
        session_id="session-docker",
        session_title="docker",
        task=SubAgentTask(role="triage", objective="triage", model="deepseek-v4-flash", target_path=str(sample)),
        core_notes=[],
        objective="验证 docker runtime",
        target_path=str(sample),
        coordination_dir=str(settings.runtime_dir / "session-docker" / "coordination"),
        peer_count=1,
    )

    captured: dict[str, tuple] = {}

    class FakeProcess:
        returncode = 0

        async def communicate(self):
            runtime_dir = settings.runtime_dir / payload.session_id / payload.task.id
            result = SubAgentResult(
                task_id=payload.task.id,
                status=SubAgentStatus.COMPLETED,
                summary="done",
            )
            (runtime_dir / "result.json").write_text(
                json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            (runtime_dir / "container.cid").write_text("cid-test-123\n", encoding="utf-8")
            return b"", b""

    async def fake_create_subprocess_exec(*args, **kwargs):
        captured["args"] = args
        return FakeProcess()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)

    result = await runtime.run(payload)
    docker_args = captured["args"]

    assert "--network" in docker_args
    assert "none" in docker_args
    assert "--cidfile" in docker_args
    assert f"{settings.runtime_dir / payload.session_id / 'coordination'}:/coordination" in docker_args
    assert f"IDA_HEADLESS_PATH={settings.ida_headless_path}" in docker_args
    assert f"{settings.host_ida_install_dir}:{settings.host_ida_install_dir}:ro" in docker_args
    assert result.container_id == "cid-test-123"


@pytest.mark.asyncio
async def test_docker_runtime_stages_external_target_into_runtime_dir(tmp_path: Path, monkeypatch):
    settings = build_settings(tmp_path)
    settings.host_workspace_dir = tmp_path / "workspace"
    settings.host_workspace_dir.mkdir(parents=True, exist_ok=True)
    settings.subagent_docker_image = "binary-audit-subagent:test"
    runtime = DockerSubAgentRuntime(settings)

    sample = tmp_path / "external.bin"
    sample.write_bytes(b"\x7fELFexternal")
    payload = SubAgentPayload(
        session_id="session-external",
        session_title="docker",
        task=SubAgentTask(role="triage", objective="triage", model="deepseek-v4-flash", target_path=str(sample)),
        core_notes=[],
        objective="验证 docker runtime 外部样本复制",
        target_path=str(sample),
        coordination_dir=str(settings.runtime_dir / "session-external" / "coordination"),
        peer_count=0,
    )

    class FakeProcess:
        returncode = 0

        async def communicate(self):
            runtime_dir = settings.runtime_dir / payload.session_id / payload.task.id
            result = SubAgentResult(
                task_id=payload.task.id,
                status=SubAgentStatus.COMPLETED,
                summary="done",
            )
            (runtime_dir / "result.json").write_text(
                json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            return b"", b""

    async def fake_create_subprocess_exec(*args, **kwargs):
        return FakeProcess()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)

    await runtime.run(payload)
    runtime_dir = settings.runtime_dir / payload.session_id / payload.task.id
    payload_json = json.loads((runtime_dir / "payload.json").read_text(encoding="utf-8"))
    staged_targets = list((runtime_dir / "inputs").iterdir())

    assert payload_json["target_path"].startswith("/runtime/inputs/external-")
    assert len(staged_targets) == 1
    assert staged_targets[0].read_bytes() == sample.read_bytes()


@pytest.mark.asyncio
async def test_subagent_returns_collected_evidence_when_finalize_analysis_fails(tmp_path: Path):
    settings = build_settings(tmp_path)
    sample = tmp_path / "sample.bin"
    sample.write_bytes(b"\x7fELFfailing-finalize")

    class FinalizeFailBackend(FakeLLMBackend):
        async def finalize_analysis(self, *, task, core_notes, evidence, plan, selection, interventions):
            raise RuntimeError("finalize timeout")

    worker = SubAgentWorker(settings, llm_backend=FinalizeFailBackend())

    async def fake_collect(role, target_path, publish):
        return [
            CommandEvidence(
                command_id="function_disasm",
                command=["objdump", target_path],
                return_code=0,
                stdout='{"functions":[{"name":"vuln","address":"0x401347"}]}',
            )
        ]

    async def fake_collect_follow_up(target_path, requests, publish):
        return []

    worker.toolbox.collect = fake_collect  # type: ignore[method-assign]
    worker.toolbox.collect_follow_up = fake_collect_follow_up  # type: ignore[method-assign]
    worker.toolbox.plan_follow_up = lambda role, evidence, round_index, peer_notes=None: []  # type: ignore[method-assign]

    payload = SubAgentPayload(
        session_id="session-fail",
        session_title="failing finalize",
        task=SubAgentTask(role="dynamic-analysis", objective="dynamic", model="deepseek-v4-pro", target_path=str(sample)),
        core_notes=[],
        objective="验证失败时仍保留证据",
        target_path=str(sample),
    )

    result = await worker.execute(payload)

    assert result.status == SubAgentStatus.FAILED
    assert result.error == "finalize timeout"
    assert [item.command_id for item in result.evidence] == ["function_disasm"]
