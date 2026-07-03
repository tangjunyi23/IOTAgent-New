import json
from pathlib import Path

from app.config import ROOT_DIR, Settings, ensure_directories
from app.manager import ManagerAgentService
from app.models import AuditRequest, AuditSession, CommandEvidence, SubAgentTask
from app.realtime import AuditEventBroker
from app.repository import JsonRepository


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


def test_manager_highlights_deduplicate_similar_notes(tmp_path: Path):
    settings = build_settings(tmp_path)
    manager = ManagerAgentService(settings, JsonRepository(settings), AuditEventBroker())
    request = AuditRequest(
        title="Manager Highlight Dedup",
        objective="验证关键结论去重。",
        target_path="/tmp/sample",
    )
    session = AuditSession(
        request=request,
        subagents=[
            SubAgentTask(
                role="triage",
                objective="triage",
                model="deepseek-v4-flash",
                target_path="/tmp/sample",
                promoted_notes=[
                    "主漏洞：存在栈缓冲区溢出，可覆盖返回地址。",
                    "利用条件：No canary 且 No PIE，固定基址可直接复用。",
                ],
            ),
            SubAgentTask(
                role="static-analysis",
                objective="static",
                model="deepseek-v4-flash",
                target_path="/tmp/sample",
                promoted_notes=[
                    "存在栈溢出漏洞：`fgets` 长度大于缓冲区容量。",
                    "存在显式的 ROP Gadget：`my_gadget` 等价于 `pop rdi; ret`。",
                ],
            ),
        ],
    )

    report = manager._compose_final_report(session)
    key_section = report.split("## 关键结论", 1)[1]
    if "## RCE / getshell 结论" in key_section:
        key_section = key_section.split("## RCE / getshell 结论", 1)[0]
    highlight_lines = [line for line in key_section.splitlines() if line.startswith("- ")]

    assert len(highlight_lines) == 3
    assert any("主漏洞" in line for line in highlight_lines)
    assert any("利用条件" in line for line in highlight_lines)
    assert any("ROP Gadget" in line for line in highlight_lines)
    assert not any("fgets" in line for line in highlight_lines if "主漏洞" not in line)


def test_manager_report_drops_manager_metadata_header_and_placeholder_title(tmp_path: Path):
    settings = build_settings(tmp_path)
    manager = ManagerAgentService(settings, JsonRepository(settings), AuditEventBroker())
    sample = tmp_path / "pwn"
    sample.write_bytes(b"\x7fELFreport")
    session = AuditSession(
        request=AuditRequest(
            title="样本初始审计",
            objective="不应在最终报告头部重复低价值元信息。",
            target_path=str(sample),
        ),
    )

    report = manager._compose_final_report(session)

    assert report.startswith("# pwn 深度审计报告")
    assert "## 管理代理结论" not in report
    assert "目标路径:" not in report
    assert "审计目标:" not in report
    assert "难度等级:" not in report
    assert "常规模型:" not in report
    assert "困难模型:" not in report


def test_manager_sanitizes_next_step_language_from_subagent_summary(tmp_path: Path):
    settings = build_settings(tmp_path)
    manager = ManagerAgentService(settings, JsonRepository(settings), AuditEventBroker())
    request = AuditRequest(
        title="Manager Summary Sanitizer",
        objective="验证最终报告不会暴露后续动作提示。",
        target_path="/tmp/sample",
    )
    session = AuditSession(
        request=request,
        subagents=[
            SubAgentTask(
                role="triage",
                objective="triage",
                model="deepseek-v4-flash",
                target_path="/tmp/sample",
                output_summary="\n".join(
                    [
                        "1. 已验证发现",
                        "- checksec 显示 No PIE。",
                        "3. 下一步建议",
                        "- 继续分析 get_info。",
                        "- 后续可继续做 GDB 验证。",
                    ]
                ),
            )
        ],
    )

    report = manager._compose_final_report(session)

    assert "下一步建议" not in report
    assert "继续分析" not in report
    assert "后续可继续" not in report
    assert "checksec 显示 No PIE" in report


def test_manager_report_adds_function_level_section_from_tool_evidence(tmp_path: Path):
    settings = build_settings(tmp_path)
    manager = ManagerAgentService(settings, JsonRepository(settings), AuditEventBroker())
    request = AuditRequest(
        title="Manager Function Rollup",
        objective="验证最终报告下沉到函数级。",
        target_path="/tmp/sample",
    )
    session = AuditSession(
        request=request,
        subagents=[
            SubAgentTask(
                role="triage",
                objective="triage",
                model="deepseek-v4-flash",
                target_path="/tmp/sample",
                evidence=[
                    CommandEvidence(
                        command_id="function_disasm",
                        command=["objdump", "--focus-disasm", "/tmp/sample"],
                        return_code=0,
                        stdout=(
                            '{"functions":[{"name":"main","address":"0x4011b6","stack_frame_bytes":64,'
                            '"call_sites":[{"from":"0x40123b","target":"read@plt","issue":{"type":"overflow-candidate",'
                            '"evidence":"read length=0x100 capacity≈0x40 buffer=buf"}},'
                            '{"from":"0x40124f","target":"printf@plt","issue":{"type":"format-string",'
                            '"evidence":"printf first-arg=buf"}}]}]}'
                        ),
                    ),
                    CommandEvidence(
                        command_id="function_xrefs",
                        command=["radare2", "--focus-xrefs", "/tmp/sample"],
                        return_code=0,
                        stdout=(
                            '{"functions":[{"name":"main","address":"0x4011b6","caller_count":1,'
                            '"callers":[{"function":"entry0","from":"0x401090"}]}]}'
                        ),
                    ),
                    CommandEvidence(
                        command_id="rizin_overview",
                        command=["radare2", "--structured-overview", "/tmp/sample"],
                        return_code=0,
                        stdout=(
                            '{"dangerous_xrefs":{"printf":[{"function":"main","from":"0x40124f"}],'
                            '"read":[{"function":"main","from":"0x40123b"}]}}'
                        ),
                    ),
                ],
            )
        ],
    )

    report = manager._compose_final_report(session)

    assert "## 函数级取证结论" in report
    assert "## 危险函数调用链" in report
    assert "### main @ 0x4011b6" in report
    assert "格式串" in report
    assert "输入长度超过缓冲区容量估计" in report
    assert "调用者" in report
    assert "entry0@0x401090 -> main@0x4011b6 -> printf@plt@0x40124f" in report


def test_manager_report_filters_conditional_promoted_notes(tmp_path: Path):
    settings = build_settings(tmp_path)
    manager = ManagerAgentService(settings, JsonRepository(settings), AuditEventBroker())
    request = AuditRequest(
        title="Manager Conditional Notes",
        objective="验证最终报告不会保留条件性操作指引。",
        target_path="/tmp/sample",
    )
    session = AuditSession(
        request=request,
        subagents=[
            SubAgentTask(
                role="exploit-strategy",
                objective="exploit",
                model="deepseek-v4-flash",
                target_path="/tmp/sample",
                promoted_notes=[
                    "必要时通过动态输入（如 `AAAA%p.%p`）观察输出是否包含栈数据，直接证明格式化字符串漏洞的可利用性。",
                    "现有证据已锁定输入路径，只要补全 `main` 的代码，即可立即对漏洞做出确定结论。",
                    "**No PIE + No Canary**：若存在溢出，攻击者无需绕过 ASLR 和栈保护。",
                    "已排除的事项：未发现 `/bin/sh` 等后门字符串。",
                ],
            ),
            SubAgentTask(
                role="dynamic-analysis",
                objective="dynamic",
                model="deepseek-v4-flash",
                target_path="/tmp/sample",
                promoted_notes=[
                    "**结论：未知漏洞，未建立利用上下文。** 当前证据仅能说明一旦存在漏洞，利用难度因非 PIE 和 Partial RELRO 而有所降低，但尚不能论述更多。"
                ],
            ),
        ],
    )

    report = manager._compose_final_report(session)

    assert "必要时通过动态输入" not in report
    assert "观察输出是否包含栈数据" not in report
    assert "只要补全 `main` 的代码" not in report
    assert "若存在溢出" not in report
    assert "未知漏洞" not in report
    assert "未建立利用上下文" not in report
    assert "已排除的事项" in report


def test_manager_report_adds_verified_poc_section_from_gdb_evidence(tmp_path: Path):
    settings = build_settings(tmp_path)
    manager = ManagerAgentService(settings, JsonRepository(settings), AuditEventBroker())
    request = AuditRequest(
        title="Manager Verified PoC",
        objective="验证最终报告会收口到已验证 PoC。",
        target_path="/tmp/sample",
    )
    session = AuditSession(
        request=request,
        subagents=[
            SubAgentTask(
                role="dynamic-analysis",
                objective="dynamic",
                model="deepseek-v4-pro",
                target_path="/tmp/sample",
                evidence=[
                    CommandEvidence(
                        command_id="gdb_poc",
                        command=["gdb", "-q", "-nx", "-batch", "--args", "/tmp/sample"],
                        return_code=0,
                        stdout=json.dumps(
                            {
                                "validated": True,
                                "issue_type": "format-string",
                                "function": {"name": "main", "address": "0x4011b6"},
                                "gdb_observation": {
                                    "breakpoint_line": "=> 0x40124f <main+153>: call   0x4010a0 <printf@plt>",
                                    "argument_line": '0x404080 <buf>: "FMT_PROBE.%p.%p.%p.%p\\n"',
                                },
                                "native_probe": {
                                    "stdout_preview": "Please checkin first\nFMT_PROBE.0x404080.0x100.0xdeadbeef.0x14"
                                },
                                "poc": {
                                    "command": "python3 -c 'import sys; sys.stdout.write(\"FMT_PROBE.%p.%p.%p.%p\\\\n\")' | /runtime/inputs/sample"
                                },
                                "exploit_script": {
                                    "language": "python",
                                    "content": "\n".join(
                                        [
                                            "#!/usr/bin/env python3",
                                            "from pwn import *",
                                            "BINARY = '/runtime/inputs/sample'",
                                            "PAYLOAD = b'FMT_PROBE.%p.%p.%p.%p\\n'",
                                        ]
                                    ),
                                },
                            },
                            ensure_ascii=False,
                        ),
                    )
                ],
            )
        ],
    )

    report = manager._compose_final_report(session)

    assert "## 已验证 POC" in report
    assert "## RCE / getshell 结论" in report
    assert "### main @ 0x4011b6" in report
    assert "RCE 分级: 已验证信息泄露，未到 RCE / getshell" in report
    assert "PoC 产物: 已生成可复现的 python 利用脚本" in report
    assert "漏洞利用脚本 PoC: `exploit_format-string.py`" in report
    assert "GDB 断点命中" in report
    assert "触发命令" in report
    assert "FMT_PROBE.0x404080" in report
    assert "/tmp/sample" in report
    assert "/runtime/inputs/sample" not in report
    assert "```python" in report
    assert "from pwn import *" in report
    assert "BINARY = '/tmp/sample'" in report


def test_manager_report_can_promote_rce_and_getshell_from_poc_payload(tmp_path: Path):
    settings = build_settings(tmp_path)
    manager = ManagerAgentService(settings, JsonRepository(settings), AuditEventBroker())
    request = AuditRequest(
        title="Manager Getshell Rollup",
        objective="验证 Manager 会把 PoC 里的 RCE/getshell 证据提升到主结论。",
        target_path="/tmp/sample",
    )
    session = AuditSession(
        request=request,
        subagents=[
            SubAgentTask(
                role="exploit-strategy",
                objective="exploit",
                model="deepseek-v4-pro",
                target_path="/tmp/sample",
                evidence=[
                    CommandEvidence(
                        command_id="gdb_poc",
                        command=["gdb", "-q", "-nx", "-batch", "--args", "/tmp/sample"],
                        return_code=0,
                        stdout=json.dumps(
                            {
                                "validated": True,
                                "issue_type": "overflow-candidate",
                                "function": {"name": "vuln", "address": "0x401260"},
                                "gdb_observation": {
                                    "breakpoint_line": "=> 0x401260 <vuln+96>: ret",
                                    "rip_line": "rip            0x4141414141414141",
                                    "control_offset": 72,
                                },
                                "native_probe": {
                                    "signal": "SIGSEGV",
                                },
                                "command_output": "uid=1000(tankuku) gid=1000(tankuku)",
                                "shell_observation": "sh-4.4$",
                                "exploit_script": {
                                    "language": "python",
                                    "content": "from pwn import *\nprint('shell')\n",
                                },
                            },
                            ensure_ascii=False,
                        ),
                    )
                ],
            )
        ],
    )

    report = manager._compose_final_report(session)

    assert "全局分级: 已验证 getshell" in report
    assert "shell 观测" in report
    assert "命令执行回显" in report
    assert "证据闭环: vuln @ 0x401260 / overflow-candidate / 已验证 getshell" in report
    assert "### vuln @ 0x401260" in report
    assert "gdb_poc" in report
