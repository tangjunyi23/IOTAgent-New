import asyncio

import pytest

from app.config import Settings
from app.llm import DeepSeekLLMBackend, MissingDeepSeekLLMBackend, MockLLMBackend, SimpleReply, create_llm_backend
from app.model_router import ModelSelection
from app.models import CommandEvidence, SubAgentTask


@pytest.mark.asyncio
async def test_mock_backend_summarizes_real_evidence_by_role():
    backend = MockLLMBackend()
    selection = ModelSelection(model="deepseek-v4-pro", route_reason="hard-route")

    triage_task = SubAgentTask(
        role="triage",
        objective="验证 triage 证据总结。",
        model=selection.model,
        target_path="/tmp/sample",
    )
    triage_reply = await backend.finalize_analysis(
        task=triage_task,
        core_notes=[],
        evidence=[
            CommandEvidence(
                command_id="file",
                command=["file", "/tmp/sample"],
                return_code=0,
                stdout="/tmp/sample: ELF 64-bit LSB pie executable, x86-64, dynamically linked, not stripped\n",
            ),
            CommandEvidence(
                command_id="checksec",
                command=["checksec", "--file=/tmp/sample"],
                return_code=0,
                stdout=(
                    "RELRO           STACK CANARY      NX            PIE             FILE\n"
                    "Full RELRO      Canary found      NX enabled    PIE enabled     /tmp/sample\n"
                ),
            ),
            CommandEvidence(
                command_id="elf_header",
                command=["readelf", "-h", "/tmp/sample"],
                return_code=0,
                stdout=(
                    "Type:                              DYN (Position-Independent Executable file)\n"
                    "Machine:                           Advanced Micro Devices X86-64\n"
                    "Entry point address:               0x401000\n"
                ),
            ),
        ],
        plan="计划: 先做基础证据采样。",
        selection=selection,
        interventions=[],
    )

    static_task = SubAgentTask(
        role="static-analysis",
        objective="验证静态分析证据总结。",
        model=selection.model,
        target_path="/tmp/sample",
    )
    static_reply = await backend.finalize_analysis(
        task=static_task,
        core_notes=[],
        evidence=[
            CommandEvidence(
                command_id="ida_batch",
                command=["idat", "/tmp/sample"],
                return_code=0,
                metadata={"exporter": "rootfs_elf", "artifact_count": 6},
                stdout=(
                    '{"imports_preview":["puts","read"],'
                    '"function_index_preview":[{"name":"main"},{"name":"parse_input"}],'
                    '"strings_preview":["Usage: sample <arg>"]}'
                ),
            ),
            CommandEvidence(
                command_id="angr_cfg",
                command=["python", "angr::CFGFast", "/tmp/sample"],
                return_code=0,
                stdout=(
                    '{"arch":"AMD64","entry":"0x401000","imports":["puts","read"],'
                    '"functions":[{"name":"main"},{"name":"parse_input"}]}'
                ),
            ),
        ],
        plan="计划: 恢复函数轮廓。",
        selection=selection,
        interventions=[],
    )

    rizin_task = SubAgentTask(
        role="triage",
        objective="验证 rizin 结构化证据总结。",
        model=selection.model,
        target_path="/tmp/sample",
    )
    rizin_reply = await backend.finalize_analysis(
        task=rizin_task,
        core_notes=[],
        evidence=[
            CommandEvidence(
                command_id="rizin_overview",
                command=["radare2", "--structured-overview", "/tmp/sample"],
                return_code=0,
                stdout=(
                    '{"backend":{"info":"rabin2","analysis":"radare2"},'
                    '"linked_libraries":["libc.so.6"],'
                    '"dangerous_imports":["printf","read"],'
                    '"dangerous_xrefs":{"printf":[{"function":"main","from":"0x40124f"}],'
                    '"read":[{"function":"main","from":"0x40123b"}]}}'
                ),
            ),
        ],
        plan="计划: 通过 rizin 观察导入与调用点。",
        selection=selection,
        interventions=[],
    )

    assert "样本识别" in triage_reply.content
    assert "加固状态" in triage_reply.content
    assert "ELF 头信息" in triage_reply.content
    assert "IDA 导出" in static_reply.content
    assert "angr CFGFast" in static_reply.content
    assert "Rizin 动态依赖" in rizin_reply.content
    assert "Rizin 危险导入" in rizin_reply.content
    assert "Rizin 调用点" in rizin_reply.content
    assert "核心结论" in rizin_reply.content
    assert "下一步建议" not in rizin_reply.content
    assert triage_reply.content != static_reply.content


def test_create_llm_backend_requires_deepseek_key():
    backend = create_llm_backend(Settings(deepseek_api_key=None))

    assert isinstance(backend, MissingDeepSeekLLMBackend)


@pytest.mark.asyncio
async def test_mock_backend_draft_plan_omits_disabled_tool_hint():
    backend = MockLLMBackend(Settings(deepseek_api_key=None, disabled_tool_ids_raw="afl_showmap_probe"))
    selection = ModelSelection(model="deepseek-v4-flash", route_reason="tool-hint")
    task = SubAgentTask(
        role="dynamic-analysis",
        objective="验证动态分析工具提示。",
        model=selection.model,
        target_path="/tmp/sample",
    )

    reply = await backend.draft_plan(
        task=task,
        core_notes=[],
        selection=selection,
        interventions=[],
    )

    assert "gdb_batch" in reply.content
    assert "afl_showmap_probe" not in reply.content


@pytest.mark.asyncio
async def test_deepseek_backend_allows_longer_completion_without_hard_timeout():
    class FakeMessage:
        def __init__(self, content: str) -> None:
            self.content = content

    class FakeChoice:
        def __init__(self, content: str) -> None:
            self.message = FakeMessage(content)

    class SlowResponse:
        def __init__(self, content: str) -> None:
            self.choices = [FakeChoice(content)]

    class SlowCompletions:
        async def create(self, **kwargs):
            await asyncio.sleep(0.02)
            return SlowResponse("slow but completed")

    class SlowChat:
        def __init__(self) -> None:
            self.completions = SlowCompletions()

    class SlowClient:
        def __init__(self) -> None:
            self.chat = SlowChat()

    backend = object.__new__(DeepSeekLLMBackend)
    backend.client = SlowClient()

    reply = await asyncio.wait_for(
        backend._complete(
            [{"role": "user", "content": "timeout test"}],
            ModelSelection(model="deepseek-v4-flash", route_reason="test"),
        ),
        timeout=0.2,
    )

    assert reply.content == "slow but completed"


@pytest.mark.asyncio
async def test_deepseek_draft_plan_prompt_requires_attacker_server_and_cia_evidence():
    backend = object.__new__(DeepSeekLLMBackend)
    backend.settings = Settings(deepseek_api_key="test-key")
    captured: dict[str, object] = {}

    async def fake_complete(messages, selection):
        captured["messages"] = messages
        captured["selection"] = selection
        return SimpleReply("ok")

    backend._complete = fake_complete  # type: ignore[method-assign]
    selection = ModelSelection(model="deepseek-v4-flash", route_reason="prompt-check")
    task = SubAgentTask(
        role="exploitability-review",
        objective="验证计划提示词约束。",
        model=selection.model,
        target_path="/tmp/sample",
    )

    await backend.draft_plan(
        task=task,
        core_notes=["已有初步格式串迹象。"],
        selection=selection,
        interventions=[],
    )

    messages = captured["messages"]
    assert isinstance(messages, list)
    system_prompt = messages[0]["content"]
    user_prompt = messages[1]["content"]
    assert "Attacker Condition、Server Condition 与 Security Impact（CIA）" in system_prompt
    assert "Attacker Condition（攻击者条件）" in user_prompt
    assert "Server Condition（服务器条件）" in user_prompt
    assert "Security Impact（安全影响）" in user_prompt
    assert "CIA 三要素分别会受到什么影响" in user_prompt
    assert "函数调用链分析" in system_prompt


@pytest.mark.asyncio
async def test_deepseek_finalize_prompt_requires_attacker_server_and_cia_breakdown():
    backend = object.__new__(DeepSeekLLMBackend)
    backend.settings = Settings(deepseek_api_key="test-key")
    captured: dict[str, object] = {}

    async def fake_complete(messages, selection):
        captured["messages"] = messages
        captured["selection"] = selection
        return SimpleReply("ok")

    backend._complete = fake_complete  # type: ignore[method-assign]
    selection = ModelSelection(model="deepseek-v4-pro", route_reason="prompt-check")
    task = SubAgentTask(
        role="dynamic-analysis",
        objective="验证最终总结提示词约束。",
        model=selection.model,
        target_path="/tmp/sample",
    )

    await backend.finalize_analysis(
        task=task,
        core_notes=["已有 gdb_poc 证据。"],
        evidence=[
            CommandEvidence(
                command_id="gdb_poc",
                command=["gdb", "-q", "--args", "/tmp/sample"],
                return_code=0,
                stdout='{"validated": true}',
            )
        ],
        plan="计划: 通过 gdb_poc 复核利用边界。",
        selection=selection,
        interventions=[],
    )

    messages = captured["messages"]
    assert isinstance(messages, list)
    system_prompt = messages[0]["content"]
    user_prompt = messages[1]["content"]
    assert "Attacker Condition、Server Condition 和 Security Impact（CIA）" in system_prompt
    assert "网络位置（外网/内网/本地）" in system_prompt
    assert "机密性（Confidentiality）/ 完整性（Integrity）/ 可用性（Availability）逐项说明" in system_prompt
    assert "Attacker Condition（网络位置 / 权限 / 具体触发输入）" in user_prompt
    assert "Server Condition（服务端前提 / 默认配置 / 插件或功能开关 / OS 或环境边界）" in user_prompt
    assert "Security Impact，并按 CIA 分别写机密性 / 完整性 / 可用性" in user_prompt
    assert "函数名 + 函数地址 + 调用点地址" in user_prompt
    assert "Exploit Stage（RCE / getshell 结论）" in user_prompt
