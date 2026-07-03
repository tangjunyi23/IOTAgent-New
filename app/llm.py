from __future__ import annotations

import asyncio
import json
import re
from typing import Protocol

from app.config import Settings, parse_tool_id_csv
from app.model_router import ModelSelection
from app.models import AuditRequest, CommandEvidence, SubAgentTask, ToolCapability

ROLE_PLANS = {
    "triage": "确认样本类型、加固状态、入口点与外部依赖，先判断是否值得继续做深入利用分析。",
    "static-analysis": "恢复节区、符号、导入和函数轮廓，定位后续需要深入反编译的关键代码区。",
    "dynamic-analysis": "检查装载布局、动态依赖、调试入口与覆盖采样是否能跑通，找出运行期阻塞点。",
    "exploitability-review": "结合字符串、调试信息和 CFG 结果，判断输入面与潜在内存破坏触发条件。",
    "exploit-strategy": "围绕输入点、可控数据和可利用原语，提炼出下一步利用链验证方向。",
}

ROLE_TOOL_HINTS = {
    "triage": ("file", "sha256", "checksec", "elf_header", "rizin_overview"),
    "static-analysis": ("section_headers", "symbol_table", "ida_batch", "angr_cfg"),
    "dynamic-analysis": ("program_headers", "dynamic_section", "gdb_batch", "afl_showmap_probe"),
    "exploitability-review": ("strings_preview", "checksec", "gdb_batch", "angr_cfg"),
    "exploit-strategy": ("strings_preview", "section_headers", "afl_showmap_probe", "ida_batch"),
}


def _tool_hint_for_role(
    role: str,
    disabled_tool_ids_raw: str | None = None,
    available_tools: list[ToolCapability] | None = None,
) -> str:
    disabled = parse_tool_id_csv(disabled_tool_ids_raw)
    available_ids = {
        item.tool_id
        for item in (available_tools or [])
        if item.available and item.enabled
    }
    enabled_tools = [
        tool_id
        for tool_id in ROLE_TOOL_HINTS.get(role, ())
        if tool_id not in disabled and (not available_ids or tool_id in available_ids)
    ]
    return ", ".join(enabled_tools) if enabled_tools else "按当前已启用的角色流水线执行对应工具"


class LLMReply(Protocol):
    content: str


class SimpleReply:
    def __init__(
        self,
        content: str,
        *,
        model: str | None = None,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int | None = None,
        reasoning_tokens: int = 0,
        cached_tokens: int = 0,
        llm_calls: int = 1,
    ) -> None:
        self.content = content
        self.model = model
        self.prompt_tokens = max(0, int(prompt_tokens or 0))
        self.completion_tokens = max(0, int(completion_tokens or 0))
        self.total_tokens = (
            max(0, int(total_tokens or 0))
            if total_tokens is not None
            else self.prompt_tokens + self.completion_tokens
        )
        self.reasoning_tokens = max(0, int(reasoning_tokens or 0))
        self.cached_tokens = max(0, int(cached_tokens or 0))
        self.llm_calls = max(0, int(llm_calls or 0))


class LLMBackend(Protocol):
    async def plan_session(
        self,
        *,
        request: AuditRequest,
        core_notes: list[str],
        available_tools: list[ToolCapability],
        selection: ModelSelection,
    ) -> SimpleReply:
        ...

    async def draft_plan(
        self,
        *,
        task: SubAgentTask,
        core_notes: list[str],
        selection: ModelSelection,
        interventions: list[str],
        available_tools: list[ToolCapability] | None = None,
    ) -> SimpleReply:
        ...

    async def finalize_analysis(
        self,
        *,
        task: SubAgentTask,
        core_notes: list[str],
        evidence: list[CommandEvidence],
        plan: str,
        selection: ModelSelection,
        interventions: list[str],
        available_tools: list[ToolCapability] | None = None,
    ) -> SimpleReply:
        ...

    async def draft_collaboration(
        self,
        *,
        task: SubAgentTask,
        core_notes: list[str],
        evidence: list[CommandEvidence],
        peer_messages: list[str],
        selection: ModelSelection,
        interventions: list[str],
        manager_plan_summary: str | None,
        phase_label: str,
        available_tools: list[ToolCapability] | None = None,
    ) -> SimpleReply:
        ...

    async def compress_context(
        self,
        *,
        messages: list[dict[str, str]],
        selection: ModelSelection,
    ) -> SimpleReply:
        ...


class MockLLMBackend:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings

    async def plan_session(
        self,
        *,
        request: AuditRequest,
        core_notes: list[str],
        available_tools: list[ToolCapability],
        selection: ModelSelection,
    ) -> SimpleReply:
        available_ids = ", ".join(item.tool_id for item in available_tools if item.available and item.enabled) or "无"
        return SimpleReply(
            json.dumps(
                {
                    "strategy_summary": f"围绕 {request.objective} 做多角色并行取证，优先使用 {available_ids}。",
                    "global_focus": core_notes[:4],
                    "success_criteria": [
                        "明确当前 exploit stage 是否至少推进到信息泄露、栈覆盖或 RIP 可控。",
                        "若无法到达 RCE / getshell，必须精确给出当前停止边界与阻塞原因。",
                    ],
                    "roles": [
                        {
                            "role": "triage",
                            "objective": "先确认样本属性、外部依赖与危险导入，再把重点函数广播给其他子代理。",
                            "coordination_focus": ["样本加固状态", "危险导入", "重点函数入口"],
                            "collaboration_targets": ["static-analysis", "exploit-strategy"],
                            "expected_evidence": ["危险导入与调用点", "高风险函数地址", "初始 exploit stage 判断"],
                            "stage_goal": "确认当前是否仍停留在未验证阶段，还是已经到信息泄露/溢出原语。",
                            "priority": 1,
                        },
                        {
                            "role": "static-analysis",
                            "objective": "恢复函数和调用关系，验证同伴广播的高风险函数。",
                            "coordination_focus": ["函数边界", "调用关系", "参数流向"],
                            "collaboration_targets": ["triage", "exploit-strategy"],
                            "expected_evidence": ["函数边界与地址", "调用关系", "参数与缓冲区关系"],
                            "stage_goal": "把 exploit stage 对应风险下沉到函数级证据。",
                            "priority": 2,
                        },
                    ],
                },
                ensure_ascii=False,
            )
        )

    async def draft_plan(
        self,
        *,
        task: SubAgentTask,
        core_notes: list[str],
        selection: ModelSelection,
        interventions: list[str],
        available_tools: list[ToolCapability] | None = None,
    ) -> SimpleReply:
        rendered_notes = "; ".join(core_notes[:3]) or "暂无"
        rendered_interventions = "; ".join(interventions) or "无"
        focus = ROLE_PLANS.get(task.role, "围绕目标样本收集可执行证据，并将结果整理为可继续追踪的分析结论。")
        tool_hint = _tool_hint_for_role(
            task.role,
            getattr(self.settings, "disabled_tool_ids_raw", None),
            available_tools,
        )
        return SimpleReply(
            "\n".join(
                [
                    f"子代理角色: {task.role}",
                    f"模型路由: {selection.model} ({selection.route_reason})",
                    "分析后端: local-evidence-synthesizer（未配置 DEEPSEEK_API_KEY，使用本地规则总结）",
                    f"核心笔记: {rendered_notes}",
                    f"干预指令: {rendered_interventions}",
                    f"计划: {focus}",
                    f"重点工具: {tool_hint}",
                ]
            )
        )

    async def draft_collaboration(
        self,
        *,
        task: SubAgentTask,
        core_notes: list[str],
        evidence: list[CommandEvidence],
        peer_messages: list[str],
        selection: ModelSelection,
        interventions: list[str],
        manager_plan_summary: str | None,
        phase_label: str,
        available_tools: list[ToolCapability] | None = None,
    ) -> SimpleReply:
        evidence_status = ", ".join(f"{item.command_id}={item.status}" for item in evidence[:6]) or "无"
        peer_hint = "；".join(peer_messages[:2]) or "暂无同伴消息"
        return SimpleReply(
            "\n".join(
                [
                    "1. 当前已确认",
                    f"- {task.role} 在 {phase_label} 已完成: {evidence_status}",
                    "2. 希望同伴协查",
                    f"- 若你们已定位高风险函数，请回传函数名、地址与调用点。当前已见同伴消息: {peer_hint}",
                    "3. 当前阻塞",
                    "- 若关键工具失败，请其他角色用已完成证据补齐同一结论链。",
                ]
            )
        )

    async def finalize_analysis(
        self,
        *,
        task: SubAgentTask,
        core_notes: list[str],
        evidence: list[CommandEvidence],
        plan: str,
        selection: ModelSelection,
        interventions: list[str],
        available_tools: list[ToolCapability] | None = None,
    ) -> SimpleReply:
        findings, risks, next_steps = self._build_evidence_summary(task.role, evidence)
        tool_status = ", ".join(f"{item.command_id}={item.status}" for item in evidence) or "无工具输出"
        core_conclusion = self._build_core_conclusion(findings, risks, next_steps)
        return SimpleReply(
            "\n".join(
                [
                    f"[{task.role}] 深度审计摘要",
                    "分析后端: local-evidence-synthesizer（未配置 DEEPSEEK_API_KEY，使用本地规则总结）",
                    f"路由模型: {selection.model}",
                    f"计划摘要: {self._extract_plan_line(plan)}",
                    *[f"- {item}" for item in findings[:8]],
                    f"- 利用性判断: {'；'.join(risks[:3]) if risks else '当前证据未显示明确的新漏洞原语。'}",
                    f"- 核心结论: {core_conclusion}",
                    f"- 工具调用概览: {tool_status}",
                    (
                        f"- 干预记录: {'；'.join(interventions[:2])}"
                        if interventions
                        else "- 干预记录: 无"
                    ),
                ]
            )
        )

    async def compress_context(
        self,
        *,
        messages: list[dict[str, str]],
        selection: ModelSelection,
    ) -> SimpleReply:
        # Local mock: return a compact marker so tests can exercise the
        # compression observer without a real LLM call.
        return SimpleReply(
            "[compressed context summary]",
            model=selection.model,
        )

    def _build_evidence_summary(
        self,
        role: str,
        evidence: list[CommandEvidence],
    ) -> tuple[list[str], list[str], list[str]]:
        findings: list[str] = []
        risks: list[str] = []
        next_steps: list[str] = []

        for item in evidence:
            if item.status == "completed":
                self._append_completed_summary(item, findings, risks, next_steps)
                continue

            if item.status == "unavailable":
                findings.append(f"{item.command_id} 不可用: {self._first_line(item.stderr) or '运行环境未提供该工具。'}")
                if item.command_id == "rizin_overview":
                    next_steps.append("安装 rizin/rz-bin 后补齐文件概览、字符串与函数交叉验证结果。")
                if item.command_id == "angr_cfg":
                    next_steps.append("确认服务进程使用项目 .venv 启动，避免 angr 模块在运行时缺失。")
                continue

            if item.status == "skipped":
                findings.append(f"{item.command_id} 已跳过: {self._first_line(item.stderr) or '该样本不满足当前工具执行前提。'}")
                continue

            if item.status == "timeout":
                findings.append(f"{item.command_id} 超时: {self._first_line(item.stderr) or '分析时间超过配置阈值。'}")
                risks.append(f"{item.command_id} 在当前超时阈值内未完成，说明该路径的分析成本较高。")
                next_steps.append(f"为 {item.command_id} 提供更长的超时或更聚焦的输入参数。")
                continue

            findings.append(f"{item.command_id} 失败: {self._first_line(item.stderr) or '工具执行未成功返回。'}")
            if item.command_id == "afl_showmap_probe":
                risks.append("覆盖探测未跑通，当前还不能确认该样本在无参数模式下是否存在稳定可执行路径。")
                next_steps.append("为 AFL++ 提供最小可运行参数或 stdin 语料，再验证覆盖图是否能够生成。")
            elif item.command_id == "ida_batch":
                risks.append("IDA 导出失败会直接削弱函数级静态恢复质量。")
                next_steps.append("检查 IDA 安装目录、idat 可执行文件和 rootfs_elf 导出脚本是否一致。")
            elif item.command_id == "angr_cfg":
                risks.append("angr CFG 未产出时，跨函数控制流关系仍然不完整。")
                next_steps.append("确认 angr 依赖已装入运行时，并对目标单独做 CFGFast 烟雾测试。")

        if role == "triage" and not any("加固状态" in item for item in findings):
            next_steps.append("补齐样本加固属性与装载方式，避免后续利用性判断失焦。")
        if role == "static-analysis" and not any("IDA" in item or "angr" in item for item in findings):
            next_steps.append("继续补齐函数恢复、导入引用和节区布局信息。")
        if role == "dynamic-analysis" and not any("动态依赖" in item or "GDB" in item for item in findings):
            next_steps.append("补充调试入口和动态链接器行为，确认运行期攻击面。")
        if role == "exploit-strategy" and not any("字符串线索" in item or "函数线索" in item for item in findings):
            next_steps.append("继续围绕输入字符串、错误提示和关键导入函数推断可控数据流。")

        return findings, risks, next_steps

    def _build_core_conclusion(
        self,
        findings: list[str],
        risks: list[str],
        next_steps: list[str],
    ) -> str:
        for entry in findings:
            if any(token in entry for token in ("格式化字符串", "溢出", "危险调用", "Rizin 调用点", "函数深度分析")):
                return entry
        if risks:
            return "；".join(risks[:2])
        if findings:
            return findings[0]
        if next_steps:
            return f"当前尚未形成漏洞定论，已将后续验证方向推进到下一轮取证：{'；'.join(next_steps[:2])}"
        return "当前证据不足以形成稳定漏洞结论。"

    def _append_completed_summary(
        self,
        item: CommandEvidence,
        findings: list[str],
        risks: list[str],
        next_steps: list[str],
    ) -> None:
        if item.command_id == "file":
            line = self._first_line(item.stdout)
            if line:
                findings.append(f"样本识别: {line}")
            lowered = line.lower()
            if "not stripped" in lowered:
                findings.append("符号状态: 未剥离，可直接结合符号和导入表定位关键逻辑。")
            elif "stripped" in lowered:
                findings.append("符号状态: 已剥离，后续更依赖字符串、导入表和反编译恢复。")
            return

        if item.command_id == "sha256":
            digest = item.stdout.strip().split()
            if digest:
                findings.append(f"样本哈希: sha256={digest[0]}")
            return

        if item.command_id == "checksec":
            compact = " ".join(item.stdout.split())
            flags: list[str] = []
            for marker in ("Full RELRO", "Partial RELRO", "No RELRO"):
                if marker in compact:
                    flags.append(marker)
            for marker in ("Canary found", "No canary found", "NX enabled", "NX disabled", "PIE enabled", "No PIE"):
                if marker in compact:
                    flags.append(marker)
            if flags:
                findings.append(f"加固状态: {', '.join(flags)}")
            if "No canary found" in compact:
                risks.append("栈 canary 缺失，若存在栈溢出则利用门槛会明显下降。")
            if "NX disabled" in compact:
                risks.append("NX 未启用，栈或堆上的代码注入风险更高。")
            if "No PIE" in compact:
                risks.append("PIE 未启用，代码段基址固定会降低 ROP/ret2libc 的定位难度。")
            return

        if item.command_id == "elf_header":
            elf_type = self._readelf_field(item.stdout, "Type")
            machine = self._readelf_field(item.stdout, "Machine")
            entry = self._readelf_field(item.stdout, "Entry point address")
            parts = [part for part in (elf_type, machine, entry and f"entry {entry}") if part]
            if parts:
                findings.append(f"ELF 头信息: {', '.join(parts)}")
            return

        if item.command_id == "section_headers":
            section_names = self._parse_section_names(item.stdout)
            if section_names:
                highlights = [name for name in (".text", ".plt", ".got", ".got.plt", ".init_array", ".fini_array", ".symtab") if name in section_names]
                findings.append(f"节区概览: 共识别 {len(section_names)} 个节区，关键节区包括 {', '.join(highlights[:6]) or section_names[0]}")
                if ".symtab" not in section_names:
                    risks.append("未见 .symtab，符号恢复会更依赖导入表与反编译结果。")
            return

        if item.command_id == "symbol_table":
            imports = self._parse_imported_symbols(item.stdout)
            if imports:
                findings.append(f"导入符号: {', '.join(imports[:8])}")
            return

        if item.command_id == "program_headers":
            header_bits: list[str] = []
            if "GNU_RELRO" in item.stdout:
                header_bits.append("GNU_RELRO")
            if "INTERP" in item.stdout:
                header_bits.append("INTERP")
            stack_line = self._find_line(item.stdout, "GNU_STACK")
            if stack_line:
                if " RWE " in f" {stack_line} " or stack_line.rstrip().endswith("RWE"):
                    header_bits.append("executable-stack")
                    risks.append("程序头显示 GNU_STACK 可执行，若配合内存破坏原语则利用难度会下降。")
                else:
                    header_bits.append("non-executable-stack")
            if header_bits:
                findings.append(f"程序头特征: {', '.join(header_bits)}")
            return

        if item.command_id == "dynamic_section":
            libs = re.findall(r"Shared library: \[(.*?)\]", item.stdout)
            if libs:
                findings.append(f"动态依赖: {', '.join(libs[:5])}")
            if "BIND_NOW" in item.stdout:
                findings.append("动态链接标志: 启用了 BIND_NOW。")
            runpath = re.findall(r"(?:RUNPATH|RPATH).*?\[(.*?)\]", item.stdout)
            if runpath:
                risks.append(f"存在运行时库搜索路径: {runpath[0]}")
            return

        if item.command_id == "rizin_overview":
            payload = self._safe_json(item.stdout)
            if isinstance(payload, dict):
                backend = payload.get("backend") or {}
                info_backend = backend.get("info") if isinstance(backend, dict) else None
                analysis_backend = backend.get("analysis") if isinstance(backend, dict) else None
                backend_parts = [
                    part
                    for part in (
                        info_backend and f"info={info_backend}",
                        analysis_backend and f"analysis={analysis_backend}",
                    )
                    if part
                ]
                if backend_parts:
                    findings.append(f"Rizin 概览后端: {', '.join(str(part) for part in backend_parts)}")

                linked_libraries = payload.get("linked_libraries") or []
                if linked_libraries:
                    findings.append(f"Rizin 动态依赖: {', '.join(str(name) for name in linked_libraries[:6])}")

                dangerous_imports = payload.get("dangerous_imports") or []
                if dangerous_imports:
                    findings.append(f"Rizin 危险导入: {', '.join(str(name) for name in dangerous_imports[:8])}")
                    if any(str(name).split("@", 1)[0] in {"gets", "system", "strcpy", "sprintf"} for name in dangerous_imports):
                        risks.append("Rizin 已识别高风险导入函数，需尽快结合调用点验证可控输入与危险参数。")

                dangerous_xrefs = payload.get("dangerous_xrefs") or {}
                if isinstance(dangerous_xrefs, dict) and dangerous_xrefs:
                    previews: list[str] = []
                    for symbol, refs in dangerous_xrefs.items():
                        if not isinstance(refs, list):
                            continue
                        for ref in refs[:2]:
                            if not isinstance(ref, dict):
                                continue
                            func_name = ref.get("function") or "unknown"
                            from_addr = ref.get("from") or "unknown"
                            previews.append(f"{symbol} <- {func_name}@{from_addr}")
                            if len(previews) >= 6:
                                break
                        if len(previews) >= 6:
                            break
                    if previews:
                        findings.append(f"Rizin 调用点: {', '.join(previews)}")
            return

        if item.command_id == "function_disasm":
            payload = self._safe_json(item.stdout)
            if isinstance(payload, dict):
                for function in payload.get("functions", []) or []:
                    if not isinstance(function, dict):
                        continue
                    function_name = str(function.get("name") or "unknown")
                    address = str(function.get("address") or "unknown")
                    stack_frame = function.get("stack_frame_bytes")
                    call_sites = function.get("call_sites") or []
                    calls = [
                        str(site.get("target"))
                        for site in call_sites
                        if isinstance(site, dict) and site.get("target")
                    ]
                    parts = [f"{function_name}@{address}"]
                    if isinstance(stack_frame, int):
                        parts.append(f"stack={hex(stack_frame)}")
                    if calls:
                        parts.append("calls=" + ",".join(item.split("@", 1)[0] for item in calls[:4]))
                    findings.append(f"函数深度分析: {', '.join(parts)}")

                    for site in call_sites:
                        if not isinstance(site, dict):
                            continue
                        issue = site.get("issue")
                        if not isinstance(issue, dict):
                            continue
                        issue_type = issue.get("type")
                        evidence = str(issue.get("evidence") or "")
                        if issue_type == "format-string":
                            findings.append(f"函数风险: {function_name} 将可写/可控数据直接作为格式串传给 printf。")
                            risks.append(f"{function_name} 存在格式化字符串漏洞迹象: {evidence}")
                        elif issue_type == "overflow-candidate":
                            findings.append(f"函数风险: {function_name} 的输入长度超过缓冲区容量估计。")
                            risks.append(f"{function_name} 存在潜在溢出迹象: {evidence}")
            return

        if item.command_id == "function_xrefs":
            payload = self._safe_json(item.stdout)
            if isinstance(payload, dict):
                for function in payload.get("functions", []) or []:
                    if not isinstance(function, dict):
                        continue
                    function_name = str(function.get("name") or "unknown")
                    caller_count = function.get("caller_count")
                    callers = function.get("callers") or []
                    if caller_count == 0:
                        findings.append(f"函数交叉引用: {function_name} 当前未发现调用者。")
                        continue
                    previews: list[str] = []
                    for caller in callers[:3]:
                        if not isinstance(caller, dict):
                            continue
                        caller_name = caller.get("function") or "unknown"
                        caller_addr = caller.get("from") or "unknown"
                        previews.append(f"{caller_name}@{caller_addr}")
                    if previews:
                        findings.append(f"函数交叉引用: {function_name} <- {', '.join(previews)}")
            return

        if item.command_id == "strings_preview":
            strings = self._interesting_strings(item.stdout)
            if strings:
                findings.append(f"字符串线索: {', '.join(strings[:6])}")
            return

        if item.command_id == "gdb_batch":
            entry = re.search(r"Entry point:\s*(0x[0-9a-fA-F]+)", item.stdout)
            if entry:
                findings.append(f"GDB 入口点: {entry.group(1)}")
            if "is .interp" in item.stdout or "in .interp" in item.stdout:
                findings.append("GDB 已读取解释器与装载段信息，可继续结合断点做入口级动态验证。")
            return

        if item.command_id == "afl_showmap_probe":
            map_size = int(item.metadata.get("map_size_bytes", 0) or 0)
            if map_size > 0:
                findings.append(f"AFL++ 覆盖探测: 已生成覆盖图，map_size_bytes={map_size}")
            else:
                findings.append("AFL++ 覆盖探测完成但未生成有效覆盖图。")
                risks.append("当前执行路径可能需要参数、stdin 语料或特定运行环境才会展开。")
                next_steps.append("为目标补充最小触发输入，再复测 afl-showmap 的覆盖输出。")
            return

        if item.command_id == "angr_cfg":
            payload = self._safe_json(item.stdout)
            if isinstance(payload, dict):
                imports = payload.get("imports") or []
                functions = payload.get("functions") or []
                arch = payload.get("arch")
                entry = payload.get("entry")
                findings.append(
                    "angr CFGFast: "
                    + ", ".join(
                        part
                        for part in (
                            arch and f"arch={arch}",
                            entry and f"entry={entry}",
                            f"imports={len(imports)}",
                            f"functions={len(functions)}",
                        )
                        if part
                    )
                )
                if imports:
                    findings.append(f"angr 导入预览: {', '.join(str(name) for name in imports[:8])}")
            return

        if item.command_id == "ida_batch":
            payload = self._safe_json(item.stdout)
            exporter = item.metadata.get("exporter")
            artifact_count = item.metadata.get("artifact_count")
            if exporter:
                findings.append(f"IDA 导出: exporter={exporter}, artifacts={artifact_count or 0}")
            if isinstance(payload, dict):
                imports_preview = payload.get("imports_preview") or []
                strings_preview = payload.get("strings_preview") or []
                function_index_preview = payload.get("function_index_preview") or []
                if imports_preview:
                    findings.append(f"IDA 导入预览: {', '.join(str(name) for name in imports_preview[:8])}")
                if function_index_preview:
                    names = [str(item.get("name", "")) for item in function_index_preview[:6] if item.get("name")]
                    if names:
                        findings.append(f"IDA 函数线索: {', '.join(names)}")
                if strings_preview:
                    findings.append(f"IDA 字符串预览: {', '.join(str(value) for value in strings_preview[:6])}")
            return

    def _first_line(self, text: str) -> str:
        for line in text.splitlines():
            line = line.strip()
            if line:
                return line
        return ""

    def _find_line(self, text: str, keyword: str) -> str:
        for line in text.splitlines():
            if keyword in line:
                return line.strip()
        return ""

    def _readelf_field(self, text: str, field_name: str) -> str:
        pattern = rf"^{re.escape(field_name)}:\s*(.+)$"
        match = re.search(pattern, text, flags=re.MULTILINE)
        return match.group(1).strip() if match else ""

    def _parse_section_names(self, text: str) -> list[str]:
        names: list[str] = []
        for line in text.splitlines():
            match = re.search(r"\[\s*\d+\]\s+([.\w$@-]+)", line)
            if match:
                names.append(match.group(1))
        return names

    def _parse_imported_symbols(self, text: str) -> list[str]:
        imports: list[str] = []
        for line in text.splitlines():
            if " UND " not in f" {line} ":
                continue
            parts = line.split()
            name = parts[-1] if parts else ""
            if (
                name
                and name != "UND"
                and not name.startswith("(")
                and re.search(r"[A-Za-z_]", name)
                and name not in imports
            ):
                imports.append(name)
        return imports

    def _extract_plan_line(self, plan: str) -> str:
        for line in plan.splitlines():
            line = line.strip()
            if line.startswith("计划:"):
                return line
        for line in reversed(plan.splitlines()):
            line = line.strip()
            if line:
                return line
        return "无"

    def _interesting_strings(self, text: str) -> list[str]:
        candidates: list[str] = []
        priorities = ("usage", "error", "fail", "open", "read", "write", "malloc", "free", "input", "flag", "/")
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if len(line) < 4:
                continue
            lowered = line.lower()
            if any(token in lowered for token in priorities):
                candidates.append(line[:80])
            if len(candidates) >= 8:
                break
        if candidates:
            return candidates
        fallback = [line.strip()[:80] for line in text.splitlines() if line.strip()]
        return fallback[:6]

    def _safe_json(self, text: str):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None


class MissingLLMBackend:
    def __init__(self, message: str | None = None) -> None:
        self.message = message or "OpenAI-compatible API key is not configured. Local fallback is disabled."

    async def plan_session(
        self,
        *,
        request: AuditRequest,
        core_notes: list[str],
        available_tools: list[ToolCapability],
        selection: ModelSelection,
    ) -> SimpleReply:
        raise RuntimeError(self.message)

    async def draft_plan(
        self,
        *,
        task: SubAgentTask,
        core_notes: list[str],
        selection: ModelSelection,
        interventions: list[str],
        available_tools: list[ToolCapability] | None = None,
    ) -> SimpleReply:
        raise RuntimeError(self.message)

    async def finalize_analysis(
        self,
        *,
        task: SubAgentTask,
        core_notes: list[str],
        evidence: list[CommandEvidence],
        plan: str,
        selection: ModelSelection,
        interventions: list[str],
        available_tools: list[ToolCapability] | None = None,
    ) -> SimpleReply:
        raise RuntimeError(self.message)

    async def draft_collaboration(
        self,
        *,
        task: SubAgentTask,
        core_notes: list[str],
        evidence: list[CommandEvidence],
        peer_messages: list[str],
        selection: ModelSelection,
        interventions: list[str],
        manager_plan_summary: str | None,
        phase_label: str,
        available_tools: list[ToolCapability] | None = None,
    ) -> SimpleReply:
        raise RuntimeError(self.message)

    async def compress_context(
        self,
        *,
        messages: list[dict[str, str]],
        selection: ModelSelection,
    ) -> SimpleReply:
        raise RuntimeError(self.message)


class OpenAICompatibleLLMBackend:
    def __init__(self, settings: Settings) -> None:
        from openai import AsyncOpenAI

        self.settings = settings
        self.client = AsyncOpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            timeout=None,
        )

    async def _complete(self, messages: list[dict[str, str]], selection: ModelSelection) -> SimpleReply:
        base_kwargs: dict[str, object] = {
            "model": selection.model,
            "messages": messages,
            "stream": False,
        }
        candidate_kwargs: list[dict[str, object]] = []

        if selection.thinking_enabled:
            candidate_kwargs.append(
                {
                    **base_kwargs,
                    "reasoning_effort": selection.reasoning_effort,
                    "extra_body": {"thinking": {"type": "enabled"}},
                }
            )
            candidate_kwargs.append(
                {
                    **base_kwargs,
                    "reasoning_effort": selection.reasoning_effort,
                }
            )
            candidate_kwargs.append(
                {
                    **base_kwargs,
                    "extra_body": {"thinking": {"type": "enabled"}},
                }
            )
        else:
            candidate_kwargs.append(
                {
                    **base_kwargs,
                    "extra_body": {"thinking": {"type": "disabled"}},
                }
            )
        candidate_kwargs.append(base_kwargs)

        response = None
        last_error: Exception | None = None
        for kwargs in candidate_kwargs:
            try:
                response = await self._call_with_retry(kwargs)
                break
            except Exception as exc:
                if not self._is_feature_compatibility_error(exc):
                    raise
                last_error = exc
                continue

        if response is None:
            assert last_error is not None
            raise last_error
        content = response.choices[0].message.content or ""
        usage = getattr(response, "usage", None)
        prompt_details = getattr(usage, "prompt_tokens_details", None) or getattr(usage, "input_tokens_details", None)
        completion_details = getattr(usage, "completion_tokens_details", None) or getattr(usage, "output_tokens_details", None)
        return SimpleReply(
            content,
            model=getattr(response, "model", None) or selection.model,
            prompt_tokens=self._usage_value(usage, "prompt_tokens"),
            completion_tokens=self._usage_value(usage, "completion_tokens"),
            total_tokens=self._usage_value(usage, "total_tokens"),
            reasoning_tokens=self._usage_value(completion_details, "reasoning_tokens"),
            cached_tokens=self._usage_value(prompt_details, "cached_tokens"),
        )

    async def compress_context(
        self,
        *,
        messages: list[dict[str, str]],
        selection: ModelSelection,
    ) -> SimpleReply:
        # Reuse _complete (with its retry + thinking-fallback logic) for the
        # compression call. The caller supplies a compression system prompt.
        return await self._complete(messages, selection)

    def _is_feature_compatibility_error(self, exc: Exception) -> bool:
        message = str(exc).lower()
        compatibility_tokens = (
            "reasoning_effort",
            "thinking",
            "unsupported",
            "unknown parameter",
            "extra_body",
            "invalid_request_error",
            "not permitted",
        )
        return any(token in message for token in compatibility_tokens)

    def _is_retryable_error(self, exc: Exception) -> bool:
        """Whether a transient server/network error is worth a backoff retry.

        Vendor-agnostic: relies on ``status_code`` attribute (OpenAI SDK and
        most OpenAI-compatible servers populate it) plus message keywords, so
        it works for any OpenAI-compatible backend, not just one provider.
        """
        # Never retry feature-compatibility errors — those need a different
        # kwargs variant, not the same one again.
        if self._is_feature_compatibility_error(exc):
            return False
        status = getattr(exc, "status_code", None)
        if isinstance(status, int) and status in (408, 409, 425, 429, 500, 502, 503, 504):
            return True
        # OpenAI SDK connection/timeout errors do not carry a status code but
        # are raised as specific types or carry recognizable messages.
        type_name = type(exc).__name__.lower()
        if "timeout" in type_name or "connection" in type_name or "connection" in type_name:
            return True
        message = str(exc).lower()
        retryable_tokens = (
            "system is busy",
            "overloaded",
            "rate limit",
            "rate_limit",
            "service unavailable",
            "temporarily unavailable",
            "try again later",
            "timeout",
            "timed out",
            "connection",
            "bad gateway",
            "internal server error",
        )
        return any(token in message for token in retryable_tokens)

    async def _call_with_retry(self, kwargs: dict[str, object]) -> object:
        """Call ``chat.completions.create`` with backoff retries on transient errors.

        Feature-compatibility errors are NOT retried here (the caller loops over
        kwargs variants for that); only transient server/network errors trigger
        a backoff retry of the same kwargs.
        """
        max_retries = max(0, int(getattr(getattr(self, "settings", None), "llm_max_retries", 3) or 0))
        base_delay = float(getattr(getattr(self, "settings", None), "llm_retry_base_delay_seconds", 0.8) or 0.0)
        last_error: Exception | None = None
        for attempt in range(max_retries + 1):
            try:
                return await self.client.chat.completions.create(**kwargs)
            except Exception as exc:
                last_error = exc
                if not self._is_retryable_error(exc):
                    raise
                if attempt >= max_retries:
                    break
                # Exponential backoff with jitter capped at 8s per sleep.
                delay = min(8.0, base_delay * (2 ** attempt))
                await asyncio.sleep(delay)
        assert last_error is not None
        raise last_error

    def _usage_value(self, payload: object, field_name: str) -> int:
        if payload is None:
            return 0
        if isinstance(payload, dict):
            value = payload.get(field_name, 0)
        else:
            value = getattr(payload, field_name, 0)
        try:
            return max(0, int(value or 0))
        except (TypeError, ValueError):
            return 0

    def _compact_text(self, text: str, *, limit: int) -> str:
        normalized = re.sub(r"\s+", " ", str(text or "")).strip()
        if len(normalized) <= limit:
            return normalized
        return normalized[: limit - 1].rstrip() + "…"

    def _evidence_priority(self, item: CommandEvidence) -> tuple[int, int]:
        command_weight = {
            "gdb_poc": 120,
            "function_disasm": 110,
            "function_xrefs": 108,
            "ida_batch": 104,
            "angr_cfg": 102,
            "rizin_overview": 100,
            "gdb_batch": 96,
            "checksec": 92,
            "strings_preview": 90,
            "afl_showmap_probe": 88,
        }
        status_weight = {
            "failed": 80,
            "timeout": 78,
            "unavailable": 76,
            "completed": 60,
            "skipped": 24,
        }
        reused_penalty = -12 if item.metadata.get("reused") else 0
        return (
            status_weight.get(item.status, 0) + command_weight.get(item.command_id, 72) + reused_penalty,
            1 if item.metadata.get("reused") else 0,
        )

    def _prioritize_evidence(self, evidence: list[CommandEvidence], *, max_items: int) -> list[CommandEvidence]:
        scored = sorted(
            enumerate(evidence),
            key=lambda pair: (self._evidence_priority(pair[1]), pair[0]),
            reverse=True,
        )
        selected = [item for _, item in scored[:max_items]]
        return selected

    def _render_evidence_block(
        self,
        evidence: list[CommandEvidence],
        *,
        stdout_limit: int,
        stderr_limit: int,
        max_items: int,
    ) -> str:
        return "\n\n".join(
            [
                f"[{item.command_id}] {' '.join(item.command)}\n"
                f"exit={item.return_code}\n"
                + (
                    f"reuse={item.metadata.get('reused_from_role', 'history')}@round-{item.metadata.get('reused_from_round', '?')}\n"
                    if item.metadata.get("reused")
                    else ""
                )
                + (
                f"stdout:\n{item.stdout[:stdout_limit]}\n"
                f"stderr:\n{item.stderr[:stderr_limit]}"
                )
                for item in self._prioritize_evidence(evidence, max_items=max_items)
            ]
        ) or "无工具证据"

    def _render_evidence_digest(self, evidence: list[CommandEvidence], *, max_items: int) -> str:
        lines: list[str] = []
        for item in self._prioritize_evidence(evidence, max_items=max_items):
            excerpt_source = item.stderr if item.status in {"failed", "timeout", "unavailable"} else item.stdout
            excerpt = self._compact_text(excerpt_source, limit=180)
            reuse_label = ""
            if item.metadata.get("reused"):
                reused_role = item.metadata.get("reused_from_role") or "history"
                reused_round = item.metadata.get("reused_from_round") or "?"
                reuse_label = f"（复用自 {reused_role}/第{reused_round}轮）"
            lines.append(
                f"- {item.command_id}{reuse_label}: {item.status}"
                + (f"；{excerpt}" if excerpt else "")
            )
        return "\n".join(lines) or "- 无工具证据"

    async def plan_session(
        self,
        *,
        request: AuditRequest,
        core_notes: list[str],
        available_tools: list[ToolCapability],
        selection: ModelSelection,
    ) -> SimpleReply:
        rendered_notes = "\n".join(f"- {item}" for item in core_notes) or "- 暂无核心笔记"
        rendered_tools = "\n".join(
            (
                f"- {item.tool_id}: 可用且已启用"
                if item.available and item.enabled
                else (
                    f"- {item.tool_id}: 可用但已关闭"
                    if item.available
                    else f"- {item.tool_id}: 不可用"
                )
            )
            for item in available_tools
        ) or "- 暂无工具清单"
        messages = [
            {
                "role": "system",
                "content": (
                    "你是漏洞审计平台的中央 ManagerAgent，负责为子代理分工。"
                    "优先复用共享记忆与已完成工具，只为未覆盖的证据缺口规划下一轮，禁止重跑已完成的基础工具链。"
                    "角色只能从 triage / static-analysis / dynamic-analysis / exploitability-review / exploit-strategy 中按需选择。"
                    "输出严格 JSON，不带 Markdown 或解释前后缀。"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"任务标题: {request.title}\n"
                    f"审计目标: {request.objective}\n"
                    f"难度: {request.difficulty}\n"
                    f"最大子代理数: {request.max_subagents}\n"
                    f"标签: {', '.join(request.tags) or '无'}\n"
                    f"分析师笔记:\n{rendered_notes}\n"
                    f"当前可用工具:\n{rendered_tools}\n\n"
                    "请输出 JSON，字段如下：\n"
                    "{\n"
                    '  "strategy_summary": "2-4 句中文摘要，写清本轮验证主线",\n'
                    '  "global_focus": ["最多 4 条需要跨角色共享的重点"],\n'
                    '  "success_criteria": ["最多 4 条，写清本轮要达成的证据判据与 RCE / getshell 边界"],\n'
                    '  "phase_plan": [\n'
                    "    {\n"
                    '      "phase": "阶段名",\n'
                    '      "goal": "该阶段目标",\n'
                    '      "owner_roles": ["主责角色"],\n'
                    '      "exit_criteria": ["阶段退出条件"]\n'
                    "    }\n"
                    "  ],\n"
                    '  "risk_watchpoints": ["最多 4 条，写清误判或卡住的真实风险"],\n'
                    '  "roles": [\n'
                    "    {\n"
                    '      "role": "必须来自允许角色集合",\n'
                    '      "objective": "该角色本轮要完成的具体任务，必须落到证据与函数级验证",\n'
                    '      "stage_goal": "该角色要把 exploit stage 推进到哪一级，或明确卡在哪一级",\n'
                    '      "expected_evidence": ["该角色预期产出的关键证据"],\n'
                    '      "coordination_focus": ["希望广播给同伴的重点函数/问题/阻塞"],\n'
                    '      "collaboration_targets": ["建议重点协作的角色"],\n'
                    '      "priority": 1\n'
                    "    }\n"
                    "  ]\n"
                    "}\n\n"
                    "要求：\n"
                    "- roles 数量在 1 到最大子代理数之间，优先保持至少 2 个角色做交叉验证\n"
                    "- stage_goal 必须显式使用 未验证 / 信息泄露 / 栈覆盖 / RIP 可控 / RCE / getshell 边界语义\n"
                    "- success_criteria 必须明确本轮要推进到上述哪一级"
                ),
            },
        ]
        return await self._complete(messages, selection)

    async def draft_plan(
        self,
        *,
        task: SubAgentTask,
        core_notes: list[str],
        selection: ModelSelection,
        interventions: list[str],
        available_tools: list[ToolCapability] | None = None,
    ) -> SimpleReply:
        rendered_notes = "\n".join(f"- {item}" for item in core_notes) or "- 暂无核心笔记"
        rendered_interventions = "\n".join(f"- {item}" for item in interventions) or "- 无"
        role_focus = ROLE_PLANS.get(task.role, "围绕样本结构、输入面和利用链线索做工具驱动分析。")
        tool_hint = _tool_hint_for_role(task.role, self.settings.disabled_tool_ids_raw, available_tools)
        rendered_tools = "\n".join(
            f"- {item.tool_id}: {'可用' if item.available and item.enabled else ('已关闭' if item.available else '不可用')}"
            for item in (available_tools or [])
        ) or "- 未提供工具状态"
        coordination_focus = "\n".join(f"- {item}" for item in task.coordination_focus) or "- 暂无"
        collaboration_targets = ", ".join(task.collaboration_targets) or "所有同伴"
        expected_evidence = "\n".join(f"- {item}" for item in task.expected_evidence) or "- 暂无"
        continuation_brief = "\n".join(f"- {item}" for item in task.continuation_brief) or "- 首轮无历史约束"
        messages = [
            {
                "role": "system",
                "content": (
                    "你是漏洞审计平台的子代理，负责给出简洁可执行的计划。"
                    "优先复用共享记忆与历史证据，不重跑已完成的基础工具。"
                    "已有崩溃证据时，不要把“再次验证崩溃”当终点；必须推进到 信息泄露 / 栈覆盖 / RIP 可控 / RCE / getshell 中明确的一级，canary/PIE/Full RELRO 阻断时也要写清当前最接近的阶段与缺步。"
                    "若上下文已有某条事实，不要在协作消息里重复广播；只广播本轮新增证据或阻塞。"
                    "严禁把外部知识伪装成已验证事实；输入证据未提供就不能声称“已验证”。"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"角色: {task.role}\n"
                    f"目标: {task.objective}\n"
                    f"角色聚焦: {role_focus}\n"
                    f"优先工具: {tool_hint}\n"
                    f"当前工具状态:\n{rendered_tools}\n"
                    f"重点协作对象: {collaboration_targets}\n"
                    f"阶段目标: {task.stage_goal or '明确当前 exploit stage 边界'}\n"
                    f"跨轮延续约束:\n{continuation_brief}\n"
                    f"需优先广播的事项:\n{coordination_focus}\n"
                    f"预期证据:\n{expected_evidence}\n"
                    f"核心笔记:\n{rendered_notes}\n"
                    f"当前干预指令:\n{rendered_interventions}\n\n"
                    "请输出三部分：\n"
                    "1. 审计计划：3-5 条，写明工具与目的\n"
                    "2. 关键漏洞假设：只写当前证据能支撑的方向，不臆造\n"
                    "3. 需采集的证据：从哪些工具结果确认什么，并覆盖 Attacker Condition（网络位置/权限/注入输入）、Server Condition（默认配置/OS/环境边界）、Security Impact（CIA 三要素）\n"
                    "额外要求：\n"
                    "- 只能规划“可用”工具，不可用工具要写替代路径\n"
                    "- 已完成 file/checksec/readelf/strings 等基础工具的，禁止重规划，除非写明补的新缺口"
                ),
            },
        ]
        return await self._complete(messages, selection)

    async def finalize_analysis(
        self,
        *,
        task: SubAgentTask,
        core_notes: list[str],
        evidence: list[CommandEvidence],
        plan: str,
        selection: ModelSelection,
        interventions: list[str],
        available_tools: list[ToolCapability] | None = None,
    ) -> SimpleReply:
        rendered_notes = "\n".join(f"- {item}" for item in core_notes) or "- 暂无核心笔记"
        rendered_interventions = "\n".join(f"- {item}" for item in interventions) or "- 无"
        rendered_evidence = self._render_evidence_block(
            evidence,
            stdout_limit=2600,
            stderr_limit=1200,
            max_items=10,
        )
        continuation_brief = "\n".join(f"- {item}" for item in task.continuation_brief) or "- 无"
        messages = [
            {
                "role": "system",
                "content": (
                    "你是漏洞审计平台的子代理，基于证据输出可执行结论。"
                    "每条发现必须引用工具名或工具输出，严禁引用未出现在证据中的外部事实/CVE/哈希对照；推断必须标“推断”。"
                    "不要写“下一步建议”或未来动作，只写已完成的取证结论。"
                    "必须显式写清当前 exploit stage：未形成原语 / 信息泄露 / 栈覆盖 / RIP 可控 / RCE / getshell；未到 RCE 时直接写明卡在哪个边界与缺步。"
                    "验证漏洞/利用链/PoC 时必须单独列出 Attacker Condition、Server Condition、Security Impact（CIA）；证据不足写“尚未证明”，某项无直接影响写“未见直接影响”。"
                    "证据里有 exploit_script/poc 时必须写明“已产出脚本化 PoC”，不只复述 GDB 命令。"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"角色: {task.role}\n"
                    f"目标: {task.objective}\n"
                    f"上一轮计划:\n{plan}\n"
                    f"跨轮延续约束:\n{continuation_brief}\n"
                    f"核心笔记:\n{rendered_notes}\n"
                    f"干预指令:\n{rendered_interventions}\n"
                    f"工具证据:\n{rendered_evidence}\n\n"
                    "请输出四部分：\n"
                    "1. 已验证发现（每条引用工具名，如下沉到函数/调用点/参数关系）\n"
                    "2. 关键函数深度分析（函数名 + 地址 + 调用点 + 危险调用链）\n"
                    "3. 利用性判断，按小标题依次写：Attacker Condition（网络位置/权限/触发输入） / Server Condition（服务端前提/默认配置/环境边界） / Security Impact（按 CIA，无直接影响写“未见直接影响”） / Exploit Stage（是否到 RCE/getshell，精确停在哪一级）\n"
                    "4. 值得提升为核心笔记的结论\n"
                    "要求：failed/unavailable 工具要说明影响；证据不足写“尚未证明”并指出缺什么；已有 exploit_script/poc 要写“已产出脚本化 PoC”。"
                ),
            },
        ]
        return await self._complete(messages, selection)

    async def draft_collaboration(
        self,
        *,
        task: SubAgentTask,
        core_notes: list[str],
        evidence: list[CommandEvidence],
        peer_messages: list[str],
        selection: ModelSelection,
        interventions: list[str],
        manager_plan_summary: str | None,
        phase_label: str,
        available_tools: list[ToolCapability] | None = None,
    ) -> SimpleReply:
        rendered_notes = "\n".join(f"- {item}" for item in core_notes) or "- 暂无核心笔记"
        rendered_evidence = self._render_evidence_digest(evidence, max_items=6)
        rendered_peers = "\n".join(f"- {item}" for item in peer_messages[-4:]) or "- 暂无同伴消息"
        rendered_interventions = "\n".join(f"- {item}" for item in interventions) or "- 无"
        coordination_focus = "\n".join(f"- {item}" for item in task.coordination_focus) or "- 暂无"
        collaboration_targets = ", ".join(task.collaboration_targets) or "所有同伴"
        continuation_brief = "\n".join(f"- {item}" for item in task.continuation_brief) or "- 无"
        messages = [
            {
                "role": "system",
                "content": (
                    "你是漏洞审计平台的子代理，正在中途协作。输出将广播到 mailbox，必须短、准、可驱动下一轮取证。"
                    "不要重复共享记忆里的基础信息，不要写未来路线图；只写已确认的新增事实、需要谁补哪段证据、当前阻塞。"
                    "明确当前 exploit stage 停在哪一级，以及谁能补足逼近 RCE / getshell 的证据。"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"阶段: {phase_label}\n"
                    f"角色: {task.role}\n"
                    f"角色目标: {task.objective}\n"
                    f"Manager 调度摘要: {manager_plan_summary or '无'}\n"
                    f"跨轮延续约束:\n{continuation_brief}\n"
                    f"重点协作对象: {collaboration_targets}\n"
                    f"需优先广播的事项:\n{coordination_focus}\n\n"
                    f"核心笔记:\n{rendered_notes}\n\n"
                    f"同伴消息:\n{rendered_peers}\n\n"
                    f"当前证据:\n{rendered_evidence}\n\n"
                    f"干预指令:\n{rendered_interventions}\n\n"
                    "请输出三部分，每部分最多 2 条 bullet：\n"
                    "1. 当前已确认\n"
                    "2. 希望同伴协查\n"
                    "3. 当前阻塞\n\n"
                    "要求：\n"
                    "- 只写已掌握的具体函数、调用点、工具状态或阻塞\n"
                    "- 若要提问，必须明确希望同伴检查的函数/工具/证据空洞\n"
                    "- 输出中文，避免套话"
                ),
            },
        ]
        return await self._complete(messages, selection)


def _is_transient_error(exc: Exception) -> bool:
    """Vendor-agnostic check for transient server/network errors worth retrying.

    Works for any OpenAI-compatible backend: relies on ``status_code`` (set by
    the OpenAI SDK and most compatible servers) plus message/type keywords.
    """
    status = getattr(exc, "status_code", None)
    if isinstance(status, int) and status in (408, 409, 425, 429, 500, 502, 503, 504):
        return True
    type_name = type(exc).__name__.lower()
    if "timeout" in type_name or "connection" in type_name:
        return True
    message = str(exc).lower()
    retryable_tokens = (
        "system is busy",
        "overloaded",
        "rate limit",
        "rate_limit",
        "service unavailable",
        "temporarily unavailable",
        "try again later",
        "timeout",
        "timed out",
        "connection",
        "bad gateway",
        "internal server error",
    )
    return any(token in message for token in retryable_tokens)


async def _retry_transient_call(
    func: object,
    settings: Settings,
    *args: object,
    **kwargs: object,
) -> object:
    """Call an awaitable ``func(*args, **kwargs)`` with exponential backoff on
    transient errors. Non-transient errors raise immediately.

    Used for connection probes / model listing where there is no kwargs-variant
    fallback, only same-call retry.
    """
    max_retries = max(0, int(getattr(settings, "llm_max_retries", 3) or 0))
    base_delay = float(getattr(settings, "llm_retry_base_delay_seconds", 0.8) or 0.0)
    last_error: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)  # type: ignore[misc]
        except Exception as exc:
            last_error = exc
            if not _is_transient_error(exc):
                raise
            if attempt >= max_retries:
                break
            delay = min(8.0, base_delay * (2 ** attempt))
            await asyncio.sleep(delay)
    assert last_error is not None
    raise last_error


async def probe_openai_compatible_connection(
    settings: Settings,
    *,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str | None = None,
) -> None:
    effective_key = (api_key if api_key is not None else settings.llm_api_key or "").strip()
    if not effective_key:
        raise RuntimeError("OpenAI-compatible API key is not configured.")
    effective_base_url = (base_url if base_url is not None else settings.llm_base_url).strip()
    effective_model = (model if model is not None else settings.manager_regular_model).strip()

    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        api_key=effective_key,
        base_url=effective_base_url,
        timeout=30.0,
    )
    try:
        errors: list[Exception] = []
        for kwargs in (
            {
                "model": effective_model,
                "messages": [{"role": "user", "content": "ping"}],
                "stream": False,
                "max_tokens": 1,
                "extra_body": {"thinking": {"type": "disabled"}},
            },
            {
                "model": effective_model,
                "messages": [{"role": "user", "content": "ping"}],
                "stream": False,
                "max_tokens": 1,
            },
        ):
            try:
                await _retry_transient_call(
                    client.chat.completions.create,
                    settings,
                    **kwargs,
                )
                errors.clear()
                break
            except Exception as exc:
                errors.append(exc)
                # Feature-compat (thinking not supported) -> try next kwargs.
                # Anything else (incl. retried-out 5xx) -> surface immediately.
                if "thinking" not in str(exc).lower():
                    raise
        if errors:
            raise errors[-1]
    finally:
        close = getattr(client, "close", None)
        if callable(close):
            result = close()
            if asyncio.iscoroutine(result):
                await result


async def list_openai_compatible_models(
    settings: Settings,
    *,
    api_key: str | None = None,
    base_url: str | None = None,
) -> list[dict[str, str | None]]:
    effective_key = (api_key if api_key is not None else settings.llm_api_key or "").strip()
    if not effective_key:
        raise RuntimeError("OpenAI-compatible API key is not configured.")
    effective_base_url = (base_url if base_url is not None else settings.llm_base_url).strip()

    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        api_key=effective_key,
        base_url=effective_base_url,
        timeout=30.0,
    )
    try:
        response = await _retry_transient_call(client.models.list, settings)
        models: list[dict[str, str | None]] = []
        for item in getattr(response, "data", []) or []:
            model_id = getattr(item, "id", None)
            if not model_id:
                continue
            models.append(
                {
                    "id": str(model_id),
                    "owned_by": getattr(item, "owned_by", None),
                }
            )
        return sorted(models, key=lambda item: item["id"] or "")
    finally:
        close = getattr(client, "close", None)
        if callable(close):
            result = close()
            if asyncio.iscoroutine(result):
                await result


def create_llm_backend(settings: Settings) -> LLMBackend:
    if settings.llm_api_key:
        return OpenAICompatibleLLMBackend(settings)
    return MissingLLMBackend()


# Backward-compatible aliases for older imports/tests.
DeepSeekLLMBackend = OpenAICompatibleLLMBackend
MissingDeepSeekLLMBackend = MissingLLMBackend
