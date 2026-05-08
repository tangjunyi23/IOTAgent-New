from pathlib import Path

import pytest

from app.config import ROOT_DIR, Settings, ensure_directories
from app.manager import ManagerAgentService
from app.models import AuditRequest, AuditSession
from app.realtime import AuditEventBroker
from app.repository import JsonRepository


class FakePlanReply:
    def __init__(self, content: str) -> None:
        self.content = content


class FakePlannerBackend:
    async def plan_session(self, *, request, core_notes, available_tools, selection):
        return FakePlanReply(
            """
            {
              "strategy_summary": "先由 triage 给出入口与危险导入，再让 static-analysis 做函数级复核。",
              "global_focus": ["main@0x4011b6", "printf/read 调用点"],
              "phase_plan": [
                {
                  "phase": "阶段 1",
                  "goal": "先锁定高风险函数与初始 exploit stage。",
                  "owner_roles": ["triage"],
                  "exit_criteria": ["main@0x4011b6 已广播"]
                }
              ],
              "risk_watchpoints": ["不要把静态迹象误写成已验证 RCE。"],
              "roles": [
                {
                  "role": "triage",
                  "objective": "确认样本加固状态、危险导入和首个高风险函数，并立刻广播 main 调用点。",
                  "stage_goal": "确认当前是否已到信息泄露或溢出原语阶段。",
                  "expected_evidence": ["main@0x4011b6", "printf/read 调用点"],
                  "coordination_focus": ["main@0x4011b6", "printf/read 调用点"],
                  "collaboration_targets": ["static-analysis"],
                  "priority": 1
                },
                {
                  "role": "static-analysis",
                  "objective": "复核 triage 提到的 main 函数，恢复参数流并确认函数级风险。",
                  "stage_goal": "把 exploit stage 下沉到函数级证据。",
                  "expected_evidence": ["read -> printf 数据流", "main 函数边界"],
                  "coordination_focus": ["main@0x4011b6", "read -> printf 数据流"],
                  "collaboration_targets": ["triage"],
                  "priority": 2
                }
              ]
            }
            """
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
        host_workspace_dir=ROOT_DIR,
        deepseek_api_key=None,
    )
    ensure_directories(settings)
    settings.progress_log_path.write_text("test progress\n", encoding="utf-8")
    return settings


@pytest.mark.asyncio
async def test_manager_uses_llm_session_plan_to_build_tasks(tmp_path: Path):
    settings = build_settings(tmp_path)
    manager = ManagerAgentService(settings, JsonRepository(settings), AuditEventBroker())
    manager.llm_backend = FakePlannerBackend()

    request = AuditRequest(
        title="Manager Session Plan",
        objective="验证管理代理会先深度规划再分工。",
        target_path="/tmp/sample",
        difficulty="hard",
        max_subagents=2,
    )
    session = AuditSession(request=request, core_notes=manager._build_core_notes(request, "/tmp/sample"))

    summary, outline, tasks = await manager._plan_subagents(session)

    assert "triage" in summary
    assert "static-analysis" in summary
    assert "分阶段执行" in summary
    assert [task.role for task in tasks] == ["triage", "static-analysis"]
    assert tasks[0].collaboration_targets == ["static-analysis"]
    assert tasks[1].coordination_focus
    assert tasks[0].stage_goal
    assert tasks[0].expected_evidence
    assert outline.phase_plan[0].phase == "阶段 1"
    assert outline.risk_watchpoints
    assert "函数级" in tasks[1].objective
