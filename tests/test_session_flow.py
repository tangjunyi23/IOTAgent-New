import time
from io import BytesIO
from pathlib import Path

import app.manager as manager_module
from fastapi.testclient import TestClient

from app.config import ROOT_DIR, Settings, ensure_directories
from app.llm import DeepSeekLLMBackend, SimpleReply
from app.main import create_app
from app.models import AuditEvent, AuditRequest, AuditSession, CommandEvidence, ManagerPlanOutline, NoteEntry, SessionStatus, SubAgentStatus, SubAgentTask, utcnow
from app.toolbox import BinaryToolbox


def build_settings(tmp_path: Path) -> Settings:
    settings = Settings(
        data_dir=tmp_path / "data",
        upload_dir=tmp_path / "data" / "uploads",
        audit_dir=tmp_path / "data" / "audits",
        artifact_meta_dir=tmp_path / "data" / "artifacts",
        runtime_dir=tmp_path / "data" / "runtime",
        frontend_dir=ROOT_DIR / "frontend",
        progress_log_path=tmp_path / "docs" / "PROGRESS.md",
        knowledge_deleted_path=tmp_path / "data" / "knowledge" / "deleted_entries.json",
        env_file_path=tmp_path / ".env",
        host_workspace_dir=ROOT_DIR,
        enable_docker_runtime=False,
        deepseek_api_key="test-key",
        max_parallel_subagents=2,
        tool_timeout_seconds=5,
    )
    ensure_directories(settings)
    settings.progress_log_path.write_text("test progress\n", encoding="utf-8")
    return settings


def wait_for_completion(client: TestClient, session_id: str, timeout_seconds: float = 15.0) -> dict:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        response = client.get(f"/api/v1/audits/{session_id}")
        response.raise_for_status()
        payload = response.json()
        if payload["status"] in {"completed", "failed"}:
            return payload
        time.sleep(0.1)
    raise AssertionError(f"Session {session_id} did not finish within {timeout_seconds} seconds")


def test_session_runs_to_completion_and_exports_reports(tmp_path: Path, monkeypatch):
    quick_pipelines = {
        "triage": ["file", "sha256"],
        "static-analysis": ["file", "sha256"],
        "dynamic-analysis": ["file", "sha256"],
        "exploitability-review": ["file", "sha256"],
        "exploit-strategy": ["file", "sha256"],
    }
    monkeypatch.setattr(BinaryToolbox, "ROLE_PIPELINES", quick_pipelines)

    async def fake_draft_plan(self, *, task, core_notes, selection, interventions):
        return SimpleReply(
            "\n".join(
                [
                    "1. 审计计划",
                    "- 使用 file 和 sha256 快速确认样本基础属性。",
                    "2. 关键漏洞假设",
                    "- 当前仅做主链路回归，不提前声称存在漏洞。",
                    "3. 需要采集的证据",
                    "- 记录 file 与 sha256 的返回结果。",
                ]
            ),
            model=selection.model,
            prompt_tokens=20,
            completion_tokens=10,
        )

    async def fake_plan_session(self, *, request, core_notes, available_tools, selection):
        return SimpleReply(
            """
            {
              "strategy_summary": "先做轻量并行取证，再汇总为可导出的会话结果。",
              "global_focus": ["确认会话能完成并导出报告。"],
              "roles": [
                {
                  "role": "triage",
                  "objective": "使用 file 和 sha256 快速确认样本基础属性，并把阶段结果广播给同伴。",
                  "coordination_focus": ["样本属性", "会话主链路"],
                  "collaboration_targets": ["static-analysis"],
                  "priority": 1
                },
                {
                  "role": "static-analysis",
                  "objective": "复核 triage 的基础证据并确保报告导出链路可落盘。",
                  "coordination_focus": ["导出链路", "会话完成状态"],
                  "collaboration_targets": ["triage"],
                  "priority": 2
                }
              ]
            }
            """,
            model=selection.model,
            prompt_tokens=30,
            completion_tokens=18,
        )

    async def fake_finalize_analysis(self, *, task, core_notes, evidence, plan, selection, interventions):
        return SimpleReply(
            "\n".join(
                [
                    "1. 已验证发现",
                    "- file 已确认样本为 ELF 文件。",
                    "2. 关键函数深度分析",
                    "- 当前回归用例未下钻到具体危险函数，只验证会话编排与报告导出。",
                    "3. 利用性判断",
                    "- 现有证据不足以声明具体漏洞原语。",
                    "4. 值得提升为核心笔记的结论",
                    "- file 已确认样本为 ELF，主链路可完成导出。",
                ]
            ),
            model=selection.model,
            prompt_tokens=24,
            completion_tokens=12,
        )

    async def fake_draft_collaboration(
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
        return SimpleReply(
            "\n".join(
                [
                    "1. 当前已确认",
                    f"- {task.role} 已进入 {phase_label}。",
                    "2. 希望同伴协查",
                    "- 请同步你们已完成的工具状态。",
                    "3. 当前阻塞",
                    "- 无",
                ]
            ),
            model=selection.model,
            prompt_tokens=12,
            completion_tokens=6,
        )

    monkeypatch.setattr(DeepSeekLLMBackend, "plan_session", fake_plan_session)
    monkeypatch.setattr(DeepSeekLLMBackend, "draft_plan", fake_draft_plan)
    monkeypatch.setattr(DeepSeekLLMBackend, "draft_collaboration", fake_draft_collaboration)
    monkeypatch.setattr(DeepSeekLLMBackend, "finalize_analysis", fake_finalize_analysis)

    settings = build_settings(tmp_path)
    app = create_app(settings)
    sample = tmp_path / "sample.bin"
    sample.write_bytes(b"\x7fELFtest-audit-platform")

    with TestClient(app) as client:
        create_response = client.post(
            "/api/v1/audits",
            json={
                "title": "Session Export Smoke",
                "objective": "验证审计主链路和报告导出。",
                "target_path": str(sample),
                "difficulty": "routine",
                "max_subagents": 2,
                "analyst_notes": ["优先确认会话可以完成并导出报告。"],
                "tags": ["smoke", "report-export"],
            },
        )
        assert create_response.status_code == 200
        created = create_response.json()

        session = wait_for_completion(client, created["id"])
        assert session["status"] == "completed"
        assert session["final_report"]
        assert session["manager_plan_summary"]
        assert session["token_usage"]["total_tokens"] > 0
        assert session["manager_token_usage"]["total_tokens"] > 0
        assert session["shared_memory"]
        assert len(session["subagents"]) == 2
        assert all(task["status"] == "completed" for task in session["subagents"])
        assert all(task["token_usage"]["total_tokens"] > 0 for task in session["subagents"])

        markdown_response = client.get(f"/api/v1/audits/{created['id']}/report")
        assert markdown_response.status_code == 200
        assert markdown_response.headers["content-type"].startswith("text/markdown")
        assert "# Session Export Smoke" in markdown_response.text
        assert "## 子代理归档" in markdown_response.text

        json_response = client.get(
            f"/api/v1/audits/{created['id']}/report",
            params={"format": "json", "download": "true"},
        )
        assert json_response.status_code == 200
        assert json_response.headers["content-type"].startswith("application/json")
        assert "attachment;" in json_response.headers["content-disposition"]
        exported = json_response.json()
        assert exported["session_id"] == created["id"]
        assert exported["report_markdown"].startswith("# Session Export Smoke")
        assert exported["subagents"][0]["evidence"]


def test_uploaded_artifact_is_removed_after_session_finishes(tmp_path: Path, monkeypatch):
    quick_pipelines = {
        "triage": ["file", "sha256"],
        "static-analysis": ["file", "sha256"],
    }
    monkeypatch.setattr(BinaryToolbox, "ROLE_PIPELINES", quick_pipelines)

    async def fake_plan_session(self, *, request, core_notes, available_tools, selection):
        return SimpleReply(
            """
            {
              "strategy_summary": "验证会话完成后自动清理上传样本。",
              "global_focus": ["完成会话后应删除平台上传文件。"],
              "roles": [
                {
                  "role": "triage",
                  "objective": "使用 file 与 sha256 完成轻量回归。",
                  "coordination_focus": ["样本清理"],
                  "collaboration_targets": ["static-analysis"],
                  "priority": 1
                },
                {
                  "role": "static-analysis",
                  "objective": "复核主链路完成与会话落盘。",
                  "coordination_focus": ["报告完成"],
                  "collaboration_targets": ["triage"],
                  "priority": 2
                }
              ]
            }
            """
        )

    async def fake_draft_plan(self, *, task, core_notes, selection, interventions):
        return SimpleReply("1. 审计计划\n- 运行 file 与 sha256。\n2. 关键漏洞假设\n- 无。\n3. 需要采集的证据\n- 工具结果。")

    async def fake_finalize_analysis(self, *, task, core_notes, evidence, plan, selection, interventions):
        return SimpleReply(
            "1. 已验证发现\n- file 已确认样本为 ELF。\n2. 关键函数深度分析\n- 本回归不下钻危险函数。\n3. 利用性判断\n- 无新增利用原语。\n4. 值得提升为核心笔记的结论\n- 上传样本主链路已执行完成。"
        )

    async def fake_draft_collaboration(
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
        return SimpleReply("1. 当前已确认\n- 已完成本轮证据。\n2. 希望同伴协查\n- 无。\n3. 当前阻塞\n- 无。")

    monkeypatch.setattr(DeepSeekLLMBackend, "plan_session", fake_plan_session)
    monkeypatch.setattr(DeepSeekLLMBackend, "draft_plan", fake_draft_plan)
    monkeypatch.setattr(DeepSeekLLMBackend, "finalize_analysis", fake_finalize_analysis)
    monkeypatch.setattr(DeepSeekLLMBackend, "draft_collaboration", fake_draft_collaboration)

    settings = build_settings(tmp_path)
    app = create_app(settings)

    with TestClient(app) as client:
        upload = client.post(
            "/api/v1/artifacts",
            files={"file": ("cleanup.bin", BytesIO(b"\x7fELFcleanup"), "application/octet-stream")},
        )
        assert upload.status_code == 200
        artifact = upload.json()
        stored_path = Path(artifact["stored_path"])
        assert stored_path.exists()

        create_response = client.post(
            "/api/v1/audits",
            json={
                "title": "Artifact Cleanup Smoke",
                "objective": "验证会话结束后平台上传样本会自动清理。",
                "artifact_id": artifact["id"],
                "difficulty": "routine",
                "max_subagents": 2,
            },
        )
        assert create_response.status_code == 200
        created = create_response.json()

        session = wait_for_completion(client, created["id"])
        assert session["status"] == "completed"
        assert not stored_path.exists()
        assert not (settings.artifact_meta_dir / f"{artifact['id']}.json").exists()


def test_progress_document_is_not_exposed_by_api(tmp_path: Path):
    settings = build_settings(tmp_path)
    app = create_app(settings)

    with TestClient(app) as client:
        response = client.get("/api/v1/progress")
        assert response.status_code == 404


def test_create_audit_is_rejected_when_deepseek_backend_is_not_ready(tmp_path: Path):
    settings = build_settings(tmp_path)
    settings.deepseek_api_key = None
    app = create_app(settings)
    sample = tmp_path / "missing-key.bin"
    sample.write_bytes(b"\x7fELFmissing-key")

    with TestClient(app) as client:
        runtime = client.get("/api/v1/runtime")
        assert runtime.status_code == 200
        runtime_payload = runtime.json()
        assert runtime_payload["llm_backend"] == "MissingDeepSeekLLMBackend"
        assert runtime_payload["llm_provider"] == "deepseek"
        assert runtime_payload["llm_status"] == "missing_api_key"
        assert runtime_payload["llm_configured"] is False
        assert "Local fallback is disabled" in runtime_payload["llm_error"]

        create_response = client.post(
            "/api/v1/audits",
            json={
                "title": "Missing DeepSeek Key",
                "objective": "验证未配置 DeepSeek 时会在入口处拒绝创建审计。",
                "target_path": str(sample),
                "difficulty": "routine",
                "max_subagents": 1,
            },
        )
        assert create_response.status_code == 409
        assert "Local fallback is disabled" in create_response.json()["detail"]

        listed = client.get("/api/v1/audits")
        assert listed.status_code == 200
        assert listed.json() == []


def test_uploaded_elf_artifact_is_saved_with_execute_bits(tmp_path: Path):
    settings = build_settings(tmp_path)
    app = create_app(settings)

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/artifacts",
            files={"file": ("pwn", BytesIO(b"\x7fELFtest-upload"), "application/octet-stream")},
        )
        assert response.status_code == 200
        stored_path = Path(response.json()["stored_path"])
        assert stored_path.exists()
        assert stored_path.stat().st_mode & 0o111


def test_delete_audit_removes_runtime_and_uploaded_artifact(tmp_path: Path):
    settings = build_settings(tmp_path)
    app = create_app(settings)

    with TestClient(app) as client:
        upload = client.post(
            "/api/v1/artifacts",
            files={"file": ("delete-me", BytesIO(b"\x7fELFdelete-me"), "application/octet-stream")},
        )
        assert upload.status_code == 200
        artifact = upload.json()

        session = AuditSession(
            request=AuditRequest(
                title="Delete Session",
                objective="验证删除任务会清理运行目录与附件。",
                artifact_id=artifact["id"],
                difficulty="routine",
            ),
            status=SessionStatus.COMPLETED,
            subagents=[
                SubAgentTask(
                    role="triage",
                    objective="完成删除回归测试。",
                    model="deepseek-v4-flash",
                    target_path=artifact["stored_path"],
                    status=SubAgentStatus.COMPLETED,
                    promoted_notes=["checksec 已确认样本可进入后续利用评估。"],
                    finished_at=utcnow(),
                )
            ],
            final_report="# Delete Session",
        )
        app.state.repository.save_session(session)
        runtime_dir = settings.runtime_dir / session.id
        runtime_dir.mkdir(parents=True, exist_ok=True)
        (runtime_dir / "marker.txt").write_text("runtime marker\n", encoding="utf-8")

        response = client.delete(f"/api/v1/audits/{session.id}")
        assert response.status_code == 204
        assert not (settings.audit_dir / f"{session.id}.json").exists()
        assert not runtime_dir.exists()
        assert not Path(artifact["stored_path"]).exists()
        assert not (settings.artifact_meta_dir / f"{artifact['id']}.json").exists()


def test_delete_audit_is_idempotent_for_missing_session(tmp_path: Path):
    settings = build_settings(tmp_path)
    app = create_app(settings)

    with TestClient(app) as client:
        missing_session_id = "missing-session-id"

        first = client.delete(f"/api/v1/audits/{missing_session_id}")
        second = client.delete(f"/api/v1/audits/{missing_session_id}")

        assert first.status_code == 204
        assert second.status_code == 204


def test_knowledge_entry_can_be_deleted_from_history(tmp_path: Path):
    settings = build_settings(tmp_path)
    app = create_app(settings)
    sample = tmp_path / "knowledge.bin"
    sample.write_bytes(b"\x7fELFknowledge")

    with TestClient(app) as client:
        session = AuditSession(
            request=AuditRequest(
                title="Knowledge Session",
                objective="验证知识库历史删除。",
                target_path=str(sample),
                difficulty="routine",
            ),
            status=SessionStatus.COMPLETED,
            subagents=[
                SubAgentTask(
                    role="exploitability-review",
                    objective="沉淀一条知识库历史。",
                    model="deepseek-v4-flash",
                    target_path=str(sample),
                    status=SubAgentStatus.COMPLETED,
                    promoted_notes=["`function_disasm` 显示 main 将可控数据直接作为 printf 格式串。"],
                    finished_at=utcnow(),
                )
            ],
            final_report="# Knowledge Session",
        )
        app.state.repository.save_session(session)

        listed = client.get("/api/v1/knowledge")
        assert listed.status_code == 200
        entries = listed.json()
        assert len(entries) == 1

        deleted = client.delete(f"/api/v1/knowledge/{entries[0]['id']}")
        assert deleted.status_code == 204

        relisted = client.get("/api/v1/knowledge")
        assert relisted.status_code == 200
        assert relisted.json() == []
        assert settings.knowledge_deleted_path.exists()


def test_knowledge_entries_are_selected_and_capped(tmp_path: Path):
    settings = build_settings(tmp_path)
    app = create_app(settings)
    sample = tmp_path / "knowledge-cap.bin"
    sample.write_bytes(b"\x7fELFknowledge-cap")

    with TestClient(app) as client:
        session = AuditSession(
            request=AuditRequest(
                title="Knowledge Cap Session",
                objective="验证知识库只沉淀流程与危险点。",
                target_path=str(sample),
                difficulty="routine",
            ),
            status=SessionStatus.COMPLETED,
            manager_plan_summary="\n".join(
                [
                    "## 总体规划",
                    "- 围绕格式化字符串与利用链边界做精确取证。",
                    "## 跨角色重点",
                    "- printf 格式串写原语",
                    "- GOT 覆写到 system",
                    "## 成功判据",
                    "- 报告必须明确 RCE / getshell 边界",
                ]
            ),
            core_notes=[
                NoteEntry(content="任务标题: Knowledge Cap Session", source="manager", is_core=True),
            ],
            subagents=[
                SubAgentTask(
                    role="exploitability-review",
                    objective="沉淀危险点。",
                    model="deepseek-v4-flash",
                    target_path=str(sample),
                    status=SubAgentStatus.COMPLETED,
                    promoted_notes=[
                        "普通观察：欢迎语会在首次输入后打印。",
                        "vuln 存在格式化字符串漏洞，可推进到 RCE。",
                        "main 存在 getshell 利用链闭环。",
                        "输入长度检查会影响动态调试脚本的构造顺序。",
                    ],
                    finished_at=utcnow(),
                )
            ],
            final_report="# Knowledge Cap Session",
        )
        app.state.repository.save_session(session)

        listed = client.get("/api/v1/knowledge")
        assert listed.status_code == 200
        entries = listed.json()
        assert 1 <= len(entries) <= 3
        assert any(item["text"].startswith("流程摘要：") for item in entries)
        assert sum(1 for item in entries if item["text"].startswith("危险点：")) <= 2
        assert all("普通观察" not in item["text"] for item in entries)
        assert all("输入长度检查" not in item["text"] for item in entries)


def test_audit_list_compact_mode_trims_heavy_fields(tmp_path: Path):
    settings = build_settings(tmp_path)
    app = create_app(settings)
    sample = tmp_path / "compact.bin"
    sample.write_bytes(b"\x7fELFcompact")

    with TestClient(app) as client:
        session = AuditSession(
            request=AuditRequest(
                title="Compact Session",
                objective="验证列表接口返回轻量会话。",
                target_path=str(sample),
                difficulty="routine",
            ),
            status=SessionStatus.COMPLETED,
            manager_plan_summary="## 总体规划\n- 锁定函数级证据。",
            manager_plan=ManagerPlanOutline(
                strategy_summary="锁定函数级证据。",
                global_focus=["main@0x4011b6"],
            ),
            core_notes=[
                NoteEntry(content="核心笔记", source="manager", is_core=True),
            ],
            events=[
                AuditEvent(kind="session_completed", message="Session completed"),
            ],
            subagents=[
                SubAgentTask(
                    role="static-analysis",
                    objective="生成大体量 evidence。",
                    model="deepseek-v4-flash",
                    target_path=str(sample),
                    status=SubAgentStatus.COMPLETED,
                    evidence=[
                        CommandEvidence(
                            command_id="function_disasm",
                            command=["objdump", "-d", str(sample)],
                            return_code=0,
                            tool_name="objdump",
                            stdout="A" * 4096,
                            stderr="B" * 2048,
                        )
                    ],
                    promoted_notes=["vuln 存在格式化字符串漏洞，可推进到 RCE。"],
                    output_summary="已确认函数级漏洞与利用边界。",
                    finished_at=utcnow(),
                )
            ],
            final_report="# Compact Session\n\n- 已生成完整报告。",
        )
        app.state.repository.save_session(session)

        listed = client.get("/api/v1/audits", params={"compact": "true"})
        assert listed.status_code == 200
        compact_session = listed.json()[0]
        assert compact_session["core_notes"] == []
        assert compact_session["manager_plan_summary"] is None
        assert compact_session["manager_plan"] is None
        assert compact_session["final_report"] is None
        assert compact_session["subagents"][0]["evidence"][0]["stdout"] == ""
        assert compact_session["subagents"][0]["evidence"][0]["stderr"] == ""
        assert compact_session["subagents"][0]["evidence"][0]["metadata"] == {}

        detail = client.get(f"/api/v1/audits/{session.id}")
        assert detail.status_code == 200
        full_session = detail.json()
        assert full_session["manager_plan"]["strategy_summary"] == "锁定函数级证据。"
        assert full_session["subagents"][0]["evidence"][0]["stdout"] == "A" * 4096
        assert full_session["final_report"].startswith("# Compact Session")


def test_deepseek_settings_can_be_saved_and_checked(tmp_path: Path, monkeypatch):
    settings = build_settings(tmp_path)
    settings.deepseek_api_key = None
    app = create_app(settings)

    async def fake_probe(probe_settings, api_key=None):
        assert probe_settings is app.state.manager.settings
        assert api_key is None or api_key == "sk-new-key-1234"

    monkeypatch.setattr(manager_module, "probe_deepseek_connection", fake_probe)

    with TestClient(app) as client:
        updated = client.put("/api/v1/settings/deepseek", json={"api_key": "sk-new-key-1234"})
        assert updated.status_code == 200
        payload = updated.json()
        assert payload["configured"] is True
        assert payload["key_preview"].startswith("sk-n")
        assert 'DEEPSEEK_API_KEY="sk-new-key-1234"' in settings.env_file_path.read_text(encoding="utf-8")

        checked = client.post("/api/v1/settings/deepseek/check", json={})
        assert checked.status_code == 200
        result = checked.json()
        assert result["available"] is True
        assert result["status"] == "ready"


def test_system_settings_can_be_hot_updated_and_change_upload_target(tmp_path: Path):
    settings = build_settings(tmp_path)
    app = create_app(settings)
    new_upload_dir = tmp_path / "hot" / "uploads"
    new_runtime_dir = tmp_path / "hot" / "runtime"

    with TestClient(app) as client:
        current = client.get("/api/v1/settings/system")
        assert current.status_code == 200
        assert current.json()["upload_dir"] == str(settings.upload_dir)

        updated = client.put(
            "/api/v1/settings/system",
            json={
                "deepseek_base_url": "https://api.deepseek.local",
                "manager_regular_model": "deepseek-v4-test",
                "upload_dir": str(new_upload_dir),
                "runtime_dir": str(new_runtime_dir),
                "tool_timeout_seconds": 17,
                "enable_docker_runtime": False,
            },
        )
        assert updated.status_code == 200
        payload = updated.json()
        assert payload["upload_dir"] == str(new_upload_dir)
        assert payload["runtime_dir"] == str(new_runtime_dir)
        assert payload["tool_timeout_seconds"] == 17
        assert payload["deepseek_base_url"] == "https://api.deepseek.local"
        assert settings.upload_dir == new_upload_dir
        assert settings.runtime_dir == new_runtime_dir
        assert new_upload_dir.exists()
        assert new_runtime_dir.exists()

        env_text = settings.env_file_path.read_text(encoding="utf-8")
        assert f'UPLOAD_DIR="{new_upload_dir}"' in env_text
        assert f'RUNTIME_DIR="{new_runtime_dir}"' in env_text
        assert 'TOOL_TIMEOUT_SECONDS="17"' in env_text

        artifact = client.post(
            "/api/v1/artifacts",
            files={"file": ("sample.bin", BytesIO(b"ABCD"), "application/octet-stream")},
        )
        assert artifact.status_code == 200
        stored_path = Path(artifact.json()["stored_path"])
        assert stored_path.exists()
        assert stored_path.is_relative_to(new_upload_dir)


def test_tool_can_be_disabled_and_enabled_via_api(tmp_path: Path):
    settings = build_settings(tmp_path)
    app = create_app(settings)

    with TestClient(app) as client:
        listed = client.get("/api/v1/tools")
        assert listed.status_code == 200
        afl_tool = next(item for item in listed.json() if item["tool_id"] == "afl_showmap_probe")
        assert afl_tool["enabled"] is False

        enabled = client.put("/api/v1/tools/afl_showmap_probe", json={"enabled": True})
        assert enabled.status_code == 200
        assert enabled.json()["enabled"] is True
        assert "afl_showmap_probe" not in (settings.disabled_tool_ids_raw or "")

        disabled = client.put("/api/v1/tools/afl_showmap_probe", json={"enabled": False})
        assert disabled.status_code == 200
        assert disabled.json()["enabled"] is False
        assert "afl_showmap_probe" in settings.env_file_path.read_text(encoding="utf-8")


def test_manager_can_run_multiple_rounds(tmp_path: Path, monkeypatch):
    quick_pipelines = {
        "triage": ["file"],
        "static-analysis": ["file"],
        "dynamic-analysis": ["file"],
        "exploitability-review": ["file"],
        "exploit-strategy": ["file"],
    }
    monkeypatch.setattr(BinaryToolbox, "ROLE_PIPELINES", quick_pipelines)

    async def fake_plan_session(self, *, request, core_notes, available_tools, selection):
        round_two = any("第 2 轮规划" in note for note in core_notes)
        if round_two:
            assert any("共享记忆" in note or "已完成工具" in note for note in core_notes)
            return SimpleReply(
                """
                {
                  "strategy_summary": "第二轮围绕动态结论继续收敛。",
                  "global_focus": ["已完成第一轮基础取证"],
                  "roles": [
                    {
                      "role": "dynamic-analysis",
                      "objective": "第二轮复核动态证据。",
                      "coordination_focus": ["第二轮动态结论"],
                      "collaboration_targets": ["exploit-strategy"],
                      "priority": 1
                    },
                    {
                      "role": "exploit-strategy",
                      "objective": "第二轮总结 exploit stage。",
                      "coordination_focus": ["第二轮 exploit stage"],
                      "collaboration_targets": ["dynamic-analysis"],
                      "priority": 2
                    }
                  ]
                }
                """
            )
        return SimpleReply(
            """
            {
              "strategy_summary": "第一轮先做基础取证。",
              "global_focus": ["完成第一轮基础取证"],
              "roles": [
                {
                  "role": "triage",
                  "objective": "第一轮样本识别。",
                  "coordination_focus": ["样本属性"],
                  "collaboration_targets": ["static-analysis"],
                  "priority": 1
                },
                {
                  "role": "static-analysis",
                  "objective": "第一轮静态恢复。",
                  "coordination_focus": ["函数恢复"],
                  "collaboration_targets": ["triage"],
                  "priority": 2
                }
              ]
            }
            """
        )

    async def fake_draft_plan(self, *, task, core_notes, selection, interventions):
        return SimpleReply("1. 审计计划\n- 运行 file。\n2. 关键漏洞假设\n- 无。\n3. 需要采集的证据\n- file 结果。")

    async def fake_finalize_analysis(self, *, task, core_notes, evidence, plan, selection, interventions):
        return SimpleReply(
            "\n".join(
                [
                    "1. 已验证发现",
                    f"- {task.role} 已完成第 {task.round_index} 轮取证。",
                    "2. 关键函数深度分析",
                    "- 本测试只验证多轮编排。",
                    "3. 利用性判断",
                    "- 当前 exploit stage 仍未到 RCE / getshell。",
                    "4. 值得提升为核心笔记的结论",
                    f"- {task.role} 第 {task.round_index} 轮已完成。",
                ]
            )
        )

    async def fake_draft_collaboration(
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
        return SimpleReply("1. 当前已确认\n- 已完成本轮证据。\n2. 希望同伴协查\n- 无。\n3. 当前阻塞\n- 无。")

    def fake_continue(self, session, round_index):
        if round_index == 1:
            return True, "第一轮完成后继续进入第二轮规划。"
        return False, ""

    monkeypatch.setattr(DeepSeekLLMBackend, "plan_session", fake_plan_session)
    monkeypatch.setattr(DeepSeekLLMBackend, "draft_plan", fake_draft_plan)
    monkeypatch.setattr(DeepSeekLLMBackend, "finalize_analysis", fake_finalize_analysis)
    monkeypatch.setattr(DeepSeekLLMBackend, "draft_collaboration", fake_draft_collaboration)
    monkeypatch.setattr(manager_module.ManagerAgentService, "_should_continue_manager_rounds", fake_continue)

    settings = build_settings(tmp_path)
    app = create_app(settings)
    sample = tmp_path / "multi-round.bin"
    sample.write_bytes(b"\x7fELFmulti-round")

    with TestClient(app) as client:
        create_response = client.post(
            "/api/v1/audits",
            json={
                "title": "Manager Multi Round",
                "objective": "验证 Manager 会进行两轮规划与下发。",
                "target_path": str(sample),
                "difficulty": "routine",
                "max_subagents": 2,
            },
        )
        assert create_response.status_code == 200
        created = create_response.json()

        session = wait_for_completion(client, created["id"])
        assert session["status"] == "completed"
        assert session["manager_round"] == 2
        assert len(session["manager_plan_history"]) == 2
        assert len(session["subagents"]) == 4
        assert {task["round_index"] for task in session["subagents"]} == {1, 2}
        assert session["shared_memory"]
        assert any(task["reused_tool_ids"] for task in session["subagents"] if task["round_index"] == 2)
