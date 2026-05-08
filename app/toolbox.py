from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable

from app.config import Settings, parse_tool_id_csv
from app.models import AuditEvent, CommandEvidence, EventKind, ToolCapability
from app.pwn_skill import PwnSkillPack
from app.target_utils import ensure_target_executable

Publisher = Callable[[AuditEvent], Awaitable[None]]


@dataclass(frozen=True)
class ToolDescriptor:
    tool_id: str
    family: str
    mode: str
    summary: str
    candidates: tuple[str, ...] = ()


@dataclass(frozen=True)
class FocusFunction:
    name: str
    address: int
    size: int | None = None
    reason: str = ""


@dataclass(frozen=True)
class FollowUpRequest:
    command_id: str
    tool_name: str
    summary: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class IssueTarget:
    name: str
    address: int
    issue_type: str
    breakpoint: int | None = None
    size: int | None = None
    reason: str = ""
    issue_evidence: str = ""
    call_target: str = ""
    call_site: str = ""


class BinaryToolbox:
    TOOL_DESCRIPTORS: dict[str, ToolDescriptor] = {
        "file": ToolDescriptor("file", "core", "cli", "Identify binary file type", ("file",)),
        "sha256": ToolDescriptor("sha256", "core", "cli", "Compute artifact digest", ("sha256sum",)),
        "elf_header": ToolDescriptor("elf_header", "binutils", "cli", "Read ELF header", ("readelf",)),
        "section_headers": ToolDescriptor("section_headers", "binutils", "cli", "Read ELF section headers", ("readelf",)),
        "symbol_table": ToolDescriptor("symbol_table", "binutils", "cli", "Read ELF symbol table", ("readelf",)),
        "program_headers": ToolDescriptor("program_headers", "binutils", "cli", "Read ELF program headers", ("readelf",)),
        "dynamic_section": ToolDescriptor("dynamic_section", "binutils", "cli", "Read dynamic section", ("readelf",)),
        "strings_preview": ToolDescriptor("strings_preview", "binutils", "cli", "Extract printable strings", ("strings",)),
        "checksec": ToolDescriptor("checksec", "checksec", "cli", "Inspect binary hardening flags", ("checksec",)),
        "rizin_overview": ToolDescriptor("rizin_overview", "rizin", "cli", "Inspect binary metadata via rizin or compatible CLI", ("rizin", "radare2", "rz-bin", "rabin2")),
        "gdb_batch": ToolDescriptor("gdb_batch", "gdb", "cli", "Collect batch-mode debugger metadata", ("gdb",)),
        "gdb_poc": ToolDescriptor("gdb_poc", "gdb", "cli", "Validate exploit primitive with scripted GDB and emit a minimal PoC", ("gdb",)),
        "function_disasm": ToolDescriptor("function_disasm", "binutils", "cli", "Disassemble focus functions for function-level audit", ("objdump",)),
        "function_xrefs": ToolDescriptor("function_xrefs", "rizin", "cli", "Resolve callers for focus functions", ("rizin", "radare2", "rz-bin", "rabin2")),
        "afl_showmap_probe": ToolDescriptor("afl_showmap_probe", "afl++", "cli", "Probe execution path coverage with afl-showmap", ("afl-showmap",)),
        "angr_cfg": ToolDescriptor("angr_cfg", "angr", "python", "Build a lightweight CFG with angr"),
        "ida_batch": ToolDescriptor("ida_batch", "ida", "ida", "Run headless IDA metadata extraction", ("idat64", "idat")),
    }

    ROLE_PIPELINES: dict[str, list[str]] = {
        "triage": [
            "file",
            "sha256",
            "checksec",
            "elf_header",
            "rizin_overview",
        ],
        "static-analysis": [
            "section_headers",
            "symbol_table",
            "ida_batch",
            "angr_cfg",
        ],
        "dynamic-analysis": [
            "program_headers",
            "dynamic_section",
            "gdb_batch",
            "afl_showmap_probe",
        ],
        "exploitability-review": [
            "strings_preview",
            "checksec",
            "gdb_batch",
            "angr_cfg",
        ],
        "exploit-strategy": [
            "strings_preview",
            "section_headers",
            "afl_showmap_probe",
            "ida_batch",
        ],
    }

    RIZIN_XREF_SYMBOLS: tuple[str, ...] = (
        "system",
        "gets",
        "printf",
        "fprintf",
        "sprintf",
        "snprintf",
        "scanf",
        "sscanf",
        "__isoc99_scanf",
        "read",
        "recv",
        "fgets",
        "strcpy",
        "strncpy",
        "strcat",
        "strncat",
        "memcpy",
        "memmove",
        "popen",
        "execve",
        "execl",
        "execvp",
    )

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.pwn_skill = PwnSkillPack(settings)
        self._ida_script = """
import json
import os
import idautils
import ida_auto
import ida_nalt
import ida_name
import ida_segment
import idc

ida_auto.auto_wait()
output_path = os.environ["IDA_JSON_OUT"]

segments = []
for seg_ea in idautils.Segments():
    seg = ida_segment.getseg(seg_ea)
    segments.append(
        {
            "name": ida_segment.get_segm_name(seg) or "",
            "start_ea": hex(int(seg.start_ea)),
            "end_ea": hex(int(seg.end_ea)),
            "perm": int(seg.perm),
        }
    )

functions = []
for idx, ea in enumerate(idautils.Functions()):
    functions.append(
        {
            "ea": hex(int(ea)),
            "name": ida_name.get_ea_name(ea) or idc.get_func_name(ea),
        }
    )
    if idx + 1 >= 80:
        break

strings = []
try:
    string_list = idautils.Strings()
    string_list.setup()
    for idx, string in enumerate(string_list):
        strings.append({"ea": hex(int(string.ea)), "value": str(string)[:160]})
        if idx + 1 >= 40:
            break
except Exception as exc:
    strings.append({"error": str(exc)})

payload = {
    "input_file": ida_nalt.get_input_file_path(),
    "segments": segments,
    "functions": functions,
    "strings": strings,
}

with open(output_path, "w", encoding="utf-8") as handle:
    json.dump(payload, handle, ensure_ascii=False, indent=2)

idc.qexit(0)
"""

    def enabled_tool_ids(self) -> set[str]:
        return set(self.TOOL_DESCRIPTORS) - parse_tool_id_csv(self.settings.disabled_tool_ids_raw)

    def is_tool_enabled(self, tool_id: str) -> bool:
        return tool_id not in parse_tool_id_csv(self.settings.disabled_tool_ids_raw)

    def list_capabilities(self) -> list[ToolCapability]:
        return [self._build_capability(tool_id) for tool_id in self.TOOL_DESCRIPTORS]

    def plan_follow_up(
        self,
        role: str,
        evidence: list[CommandEvidence],
        round_index: int,
        peer_notes: list[str] | None = None,
    ) -> list[FollowUpRequest]:
        if not self.is_tool_enabled("function_disasm"):
            return []
        if role not in {"triage", "static-analysis", "exploitability-review", "exploit-strategy", "dynamic-analysis"}:
            return []

        focus_functions = self._identify_focus_functions(evidence, peer_notes=peer_notes)
        if not focus_functions:
            return []

        object_symbols = self._extract_object_symbols(evidence)
        pending_disasm = self._filter_uncovered_focus_functions(
            focus_functions,
            self._extract_follow_up_function_keys(evidence, "function_disasm"),
        )

        if pending_disasm and self.is_tool_enabled("function_disasm"):
            return [
                FollowUpRequest(
                    command_id="function_disasm",
                    tool_name="objdump",
                    summary="Disassemble focus functions for function-level audit",
                    payload={
                        "functions": [self._serialize_focus_function(item) for item in pending_disasm[:4]],
                        "object_symbols": object_symbols,
                    },
                )
            ]

        if (
            round_index >= 2
            and role in {"dynamic-analysis", "exploit-strategy", "exploitability-review"}
            and self.is_tool_enabled("gdb_poc")
        ):
            issue_targets = self._extract_issue_targets(evidence)
            pending_issue_targets = self._filter_issue_targets_missing_poc(evidence, issue_targets)
            if pending_issue_targets:
                return [
                    FollowUpRequest(
                        command_id="gdb_poc",
                        tool_name="gdb",
                        summary="Validate a high-risk primitive with scripted GDB and capture a minimal PoC",
                        payload={
                            "functions": pending_issue_targets[:2],
                        },
                    )
                ]

        pending_xrefs = self._filter_uncovered_focus_functions(
            focus_functions,
            self._extract_follow_up_function_keys(evidence, "function_xrefs"),
        )
        if pending_xrefs and self.is_tool_enabled("function_xrefs"):
            return [
                FollowUpRequest(
                    command_id="function_xrefs",
                    tool_name="rizin",
                    summary="Resolve callers for focus functions",
                    payload={
                        "functions": [self._serialize_focus_function(item) for item in pending_xrefs[:4]],
                    },
                )
            ]

        return []

    async def collect_follow_up(
        self,
        target_path: str,
        requests: list[FollowUpRequest],
        publish: Publisher,
    ) -> list[CommandEvidence]:
        target = Path(target_path)
        evidence: list[CommandEvidence] = []
        for request in requests:
            await publish(
                AuditEvent(
                    kind=EventKind.TOOL_INVOCATION,
                    message=f"Invoking tool {request.command_id}",
                    payload={
                        "command_key": request.command_id,
                        "tool_id": request.command_id,
                        "tool_family": request.tool_name,
                        "available": True,
                    },
                )
            )
            result = await self._dispatch_follow_up(request, target)
            evidence.append(result)
            await publish(
                AuditEvent(
                    kind=EventKind.TOOL_RESULT,
                    message=f"Tool {request.command_id} finished with status {result.status}",
                    payload={
                        "command_key": request.command_id,
                        "tool_id": request.command_id,
                        "tool_family": request.tool_name,
                        "status": result.status,
                        "return_code": result.return_code,
                        "stdout_preview": result.stdout[:400],
                        "stderr_preview": result.stderr[:400],
                    },
                )
            )
        return evidence

    async def collect(
        self,
        role: str,
        target_path: str,
        publish: Publisher,
        existing_evidence: list[CommandEvidence] | None = None,
    ) -> list[CommandEvidence]:
        target = Path(target_path)
        reused_evidence = [item.model_copy(deep=True) for item in (existing_evidence or [])]
        completed_command_ids = {
            item.command_id
            for item in reused_evidence
            if item.status == "completed" and item.command_id
        }
        pipeline = [
            tool_id
            for tool_id in self.ROLE_PIPELINES.get(role, self.ROLE_PIPELINES["triage"])
            if self.is_tool_enabled(tool_id) and tool_id not in completed_command_ids
        ]
        evidence: list[CommandEvidence] = list(reused_evidence)

        if not target.exists():
            return [
                CommandEvidence(
                    command_id="target_check",
                    command=["test", "-f", target_path],
                    return_code=1,
                    tool_name="core",
                    status="failed",
                    stderr=f"Target not found: {target_path}",
                )
            ]

        for tool_id in pipeline:
            capability = self._build_capability(tool_id)
            await publish(
                AuditEvent(
                    kind=EventKind.TOOL_INVOCATION,
                    message=f"Invoking tool {tool_id}",
                    payload={
                        "command_key": tool_id,
                        "tool_id": tool_id,
                        "tool_family": capability.family,
                        "available": capability.available,
                    },
                )
            )
            result = await self._dispatch_tool(tool_id, target)
            evidence.append(result)
            await publish(
                AuditEvent(
                    kind=EventKind.TOOL_RESULT,
                    message=f"Tool {tool_id} finished with status {result.status}",
                    payload={
                        "command_key": tool_id,
                        "tool_id": tool_id,
                        "tool_family": capability.family,
                        "status": result.status,
                        "return_code": result.return_code,
                        "stdout_preview": result.stdout[:400],
                        "stderr_preview": result.stderr[:400],
                    },
                )
            )

        return evidence

    async def _dispatch_tool(self, tool_id: str, target: Path) -> CommandEvidence:
        if tool_id == "file":
            return await asyncio.to_thread(self._run_command, tool_id, ["file", str(target)], "core")
        if tool_id == "sha256":
            return await asyncio.to_thread(self._run_command, tool_id, ["sha256sum", str(target)], "core")
        if tool_id == "elf_header":
            return await asyncio.to_thread(self._run_command, tool_id, ["readelf", "-h", str(target)], "binutils")
        if tool_id == "section_headers":
            return await asyncio.to_thread(self._run_command, tool_id, ["readelf", "-SW", str(target)], "binutils")
        if tool_id == "symbol_table":
            return await asyncio.to_thread(self._run_command, tool_id, ["readelf", "-Ws", str(target)], "binutils")
        if tool_id == "program_headers":
            return await asyncio.to_thread(self._run_command, tool_id, ["readelf", "-l", str(target)], "binutils")
        if tool_id == "dynamic_section":
            return await asyncio.to_thread(self._run_command, tool_id, ["readelf", "-d", str(target)], "binutils")
        if tool_id == "strings_preview":
            return await asyncio.to_thread(self._run_command, tool_id, ["strings", "-n", "8", "-a", str(target)], "binutils")
        if tool_id == "checksec":
            return await self._run_checksec(target)
        if tool_id == "rizin_overview":
            return await self._run_rizin(target)
        if tool_id == "gdb_batch":
            return await self._run_gdb(target)
        if tool_id == "afl_showmap_probe":
            return await self._run_afl_probe(target)
        if tool_id == "angr_cfg":
            return await self._run_angr_cfg(target)
        if tool_id == "ida_batch":
            return await self._run_ida_batch(target)
        return CommandEvidence(
            command_id=tool_id,
            command=[],
            return_code=1,
            tool_name="internal",
            status="failed",
            stderr=f"Unsupported tool_id: {tool_id}",
        )

    async def _dispatch_follow_up(self, request: FollowUpRequest, target: Path) -> CommandEvidence:
        if request.command_id == "function_disasm":
            return await asyncio.to_thread(
                self._run_function_disasm_sync,
                target,
                request.payload.get("functions", []),
                request.payload.get("object_symbols", {}),
            )
        if request.command_id == "function_xrefs":
            return await asyncio.to_thread(
                self._run_function_xrefs_sync,
                target,
                request.payload.get("functions", []),
            )
        if request.command_id == "gdb_poc":
            return await asyncio.to_thread(
                self._run_gdb_poc_sync,
                target,
                request.payload.get("functions", []),
            )
        return CommandEvidence(
            command_id=request.command_id,
            command=[],
            return_code=1,
            tool_name=request.tool_name,
            status="failed",
            stderr=f"Unsupported follow-up tool: {request.command_id}",
        )

    def _run_command(
        self,
        command_id: str,
        argv: list[str],
        tool_name: str,
        env: dict[str, str] | None = None,
    ) -> CommandEvidence:
        try:
            completed = subprocess.run(
                argv,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.settings.tool_timeout_seconds,
                check=False,
                env=env,
            )
            stdout = completed.stdout[: self.settings.tool_output_limit]
            stderr = completed.stderr[: self.settings.tool_output_limit]
            return CommandEvidence(
                command_id=command_id,
                command=argv,
                return_code=completed.returncode,
                tool_name=tool_name,
                status="completed" if completed.returncode == 0 else "failed",
                stdout=stdout,
                stderr=stderr,
            )
        except FileNotFoundError as exc:
            return CommandEvidence(
                command_id=command_id,
                command=argv,
                return_code=127,
                tool_name=tool_name,
                status="unavailable",
                stderr=str(exc),
            )
        except subprocess.TimeoutExpired as exc:
            stdout = (exc.stdout or "")[: self.settings.tool_output_limit]
            stderr = (exc.stderr or "")[: self.settings.tool_output_limit]
            return CommandEvidence(
                command_id=command_id,
                command=argv,
                return_code=124,
                tool_name=tool_name,
                status="timeout",
                stdout=stdout,
                stderr=stderr,
            )

    async def _run_checksec(self, target: Path) -> CommandEvidence:
        capability = self._build_capability("checksec")
        if not capability.available or capability.executable is None:
            return self._unavailable_evidence("checksec", "checksec", capability.summary)
        return await asyncio.to_thread(
            self._run_command,
            "checksec",
            [capability.executable, f"--file={target}"],
            "checksec",
        )

    async def _run_rizin(self, target: Path) -> CommandEvidence:
        binaries = self._resolve_rizin_binaries()
        if not binaries:
            capability = self._build_capability("rizin_overview")
            return self._unavailable_evidence("rizin_overview", "rizin", capability.summary)

        info_executable = binaries.get("rz-bin") or binaries.get("rabin2") or binaries.get("rizin") or binaries.get("radare2")
        analysis_executable = binaries.get("rizin") or binaries.get("radare2")
        return await asyncio.to_thread(self._run_rizin_sync, target, info_executable, analysis_executable)

    def _run_rizin_sync(
        self,
        target: Path,
        info_executable: str | None,
        analysis_executable: str | None,
    ) -> CommandEvidence:
        if info_executable is None and analysis_executable is None:
            return self._unavailable_evidence(
                "rizin_overview",
                "rizin",
                "Executable not found: rizin, radare2, rz-bin, rabin2",
            )

        env = self._build_command_env(info_executable or analysis_executable)
        subcommands: list[list[str]] = []
        payload: dict[str, object] = {
            "target": str(target),
            "backend": {
                "info": Path(info_executable).name if info_executable else None,
                "analysis": Path(analysis_executable).name if analysis_executable else None,
            },
        }
        errors: list[dict[str, object]] = []

        imported_functions: list[str] = []
        dangerous_imports: list[str] = []

        if info_executable is not None:
            info_command = [info_executable, "-jI", str(target)]
            info_result = self._run_command("rizin_overview", info_command, "rizin", env=env)
            subcommands.append(info_command)
            if info_result.status != "completed":
                errors.append(
                    {
                        "phase": "info",
                        "status": info_result.status,
                        "return_code": info_result.return_code,
                        "stderr": info_result.stderr[:400],
                    }
                )
            else:
                info_payload = self._load_json_payload(info_result.stdout)
                if isinstance(info_payload, dict):
                    payload["info"] = info_payload.get("info", info_payload)

            libs_command = [info_executable, "-jl", str(target)]
            libs_result = self._run_command("rizin_overview", libs_command, "rizin", env=env)
            subcommands.append(libs_command)
            if libs_result.status != "completed":
                errors.append(
                    {
                        "phase": "linked_libraries",
                        "status": libs_result.status,
                        "return_code": libs_result.return_code,
                        "stderr": libs_result.stderr[:400],
                    }
                )
            else:
                libs_payload = self._load_json_payload(libs_result.stdout)
                if isinstance(libs_payload, dict):
                    libs = libs_payload.get("libs", [])
                    if isinstance(libs, list):
                        payload["linked_libraries"] = libs[:32]

            imports_command = [info_executable, "-ji", str(target)]
            imports_result = self._run_command("rizin_overview", imports_command, "rizin", env=env)
            subcommands.append(imports_command)
            if imports_result.status != "completed":
                errors.append(
                    {
                        "phase": "imports",
                        "status": imports_result.status,
                        "return_code": imports_result.return_code,
                        "stderr": imports_result.stderr[:400],
                    }
                )
            else:
                imports_payload = self._load_json_payload(imports_result.stdout)
                if isinstance(imports_payload, dict):
                    imports = imports_payload.get("imports", [])
                    if isinstance(imports, list):
                        payload["imports"] = imports[:80]
                        imported_functions = [
                            str(entry.get("name", ""))
                            for entry in imports
                            if isinstance(entry, dict) and entry.get("type") == "FUNC" and entry.get("name")
                        ]
                        dangerous_imports = [
                            name
                            for name in imported_functions
                            if self._normalize_import_name(name) in self.RIZIN_XREF_SYMBOLS
                        ]
                        if dangerous_imports:
                            payload["dangerous_imports"] = sorted(dict.fromkeys(dangerous_imports))

        dangerous_xrefs: dict[str, list[dict[str, object]]] = {}
        if analysis_executable is not None:
            functions_command = [analysis_executable, "-q", "-c", "aa;aflj", str(target)]
            functions_result = self._run_command("rizin_overview", functions_command, "rizin", env=env)
            subcommands.append(functions_command)
            if functions_result.status != "completed":
                errors.append(
                    {
                        "phase": "functions",
                        "status": functions_result.status,
                        "return_code": functions_result.return_code,
                        "stderr": functions_result.stderr[:400],
                    }
                )
            else:
                functions_payload = self._load_json_payload(functions_result.stdout)
                if isinstance(functions_payload, list):
                    payload["functions"] = [
                        {
                            "name": entry.get("name"),
                            "offset": hex(entry.get("offset")) if isinstance(entry.get("offset"), int) else entry.get("offset"),
                            "size": entry.get("size"),
                            "stackframe": entry.get("stackframe"),
                            "nlocals": entry.get("nlocals"),
                            "signature": entry.get("signature"),
                        }
                        for entry in functions_payload[:80]
                        if isinstance(entry, dict)
                    ]

            for symbol_name in sorted(dict.fromkeys(dangerous_imports)):
                command = [analysis_executable, "-q", "-c", f"aa;axtj sym.imp.{symbol_name}", str(target)]
                xref_result = self._run_command("rizin_overview", command, "rizin", env=env)
                subcommands.append(command)
                if xref_result.status != "completed":
                    errors.append(
                        {
                            "phase": f"xrefs:{symbol_name}",
                            "status": xref_result.status,
                            "return_code": xref_result.return_code,
                            "stderr": xref_result.stderr[:400],
                        }
                    )
                    continue

                xref_payload = self._load_json_payload(xref_result.stdout)
                if not isinstance(xref_payload, list):
                    continue
                normalized_refs: list[dict[str, object]] = []
                for entry in xref_payload[:20]:
                    if not isinstance(entry, dict):
                        continue
                    from_addr = entry.get("from")
                    normalized_refs.append(
                        {
                            "from": hex(from_addr) if isinstance(from_addr, int) else from_addr,
                            "type": entry.get("type"),
                            "opcode": entry.get("opcode"),
                            "function": entry.get("fcn_name"),
                            "refname": entry.get("refname"),
                        }
                    )
                if normalized_refs:
                    dangerous_xrefs[symbol_name] = normalized_refs

        if dangerous_xrefs:
            payload["dangerous_xrefs"] = dangerous_xrefs
        if errors:
            payload["errors"] = errors

        completed_core = "info" in payload and "imports" in payload
        status = "completed" if completed_core else "failed"
        stderr = ""
        if errors:
            stderr = "; ".join(
                f"{item['phase']}={item['status']}({item['return_code']})"
                for item in errors[:6]
            )
        metadata = {
            "subcommands": subcommands,
            "analysis_backend": Path(analysis_executable).name if analysis_executable else None,
            "info_backend": Path(info_executable).name if info_executable else None,
            "dangerous_import_count": len(dangerous_imports),
            "dangerous_xref_count": sum(len(items) for items in dangerous_xrefs.values()),
        }
        return CommandEvidence(
            command_id="rizin_overview",
            command=[analysis_executable or info_executable or "rizin", "--structured-overview", str(target)],
            return_code=0 if status == "completed" else 1,
            tool_name="rizin",
            status=status,
            stdout=json.dumps(payload, ensure_ascii=False, indent=2)[: self.settings.tool_output_limit],
            stderr=stderr[: self.settings.tool_output_limit],
            metadata=metadata,
        )

    def _run_function_disasm_sync(
        self,
        target: Path,
        functions: Any,
        object_symbols: Any,
    ) -> CommandEvidence:
        if shutil.which("objdump") is None:
            return self._unavailable_evidence("function_disasm", "objdump", "Executable not found: objdump")

        serialized_functions = self._deserialize_focus_functions(functions)
        if not serialized_functions:
            return CommandEvidence(
                command_id="function_disasm",
                command=["objdump", str(target)],
                return_code=0,
                tool_name="objdump",
                status="skipped",
                stderr="No focus functions selected for disassembly",
            )

        object_size_map = {
            str(name): int(size)
            for name, size in (object_symbols or {}).items()
            if isinstance(name, str) and isinstance(size, int)
        }

        summaries: list[dict[str, Any]] = []
        subcommands: list[list[str]] = []
        errors: list[dict[str, Any]] = []
        for function in serialized_functions:
            start = function.address
            stop = function.address + (function.size or 0x90)
            argv = [
                "objdump",
                "-d",
                "-M",
                "intel",
                f"--start-address={hex(start)}",
                f"--stop-address={hex(stop)}",
                str(target),
            ]
            subcommands.append(argv)
            result = self._run_command("function_disasm", argv, "objdump")
            if result.status != "completed":
                errors.append(
                    {
                        "function": function.name,
                        "status": result.status,
                        "return_code": result.return_code,
                        "stderr": result.stderr[:400],
                    }
                )
                continue
            summaries.append(
                self._summarize_function_disassembly(
                    function,
                    result.stdout,
                    object_size_map,
                )
            )

        status = "completed" if summaries else "failed"
        payload = {
            "functions": summaries,
            "errors": errors,
        }
        return CommandEvidence(
            command_id="function_disasm",
            command=["objdump", "--focus-disasm", str(target)],
            return_code=0 if status == "completed" else 1,
            tool_name="objdump",
            status=status,
            stdout=json.dumps(payload, ensure_ascii=False, indent=2)[: self.settings.tool_output_limit],
            stderr="; ".join(f"{item['function']}={item['status']}" for item in errors[:6])[: self.settings.tool_output_limit],
            metadata={"subcommands": subcommands},
        )

    def _run_function_xrefs_sync(self, target: Path, functions: Any) -> CommandEvidence:
        binaries = self._resolve_rizin_binaries()
        analysis_executable = binaries.get("rizin") or binaries.get("radare2")
        if analysis_executable is None:
            return self._unavailable_evidence("function_xrefs", "rizin", "Executable not found: rizin, radare2")

        env = self._build_command_env(analysis_executable)
        serialized_functions = self._deserialize_focus_functions(functions)
        if not serialized_functions:
            return CommandEvidence(
                command_id="function_xrefs",
                command=[analysis_executable, str(target)],
                return_code=0,
                tool_name="rizin",
                status="skipped",
                stderr="No focus functions selected for xref analysis",
            )

        summaries: list[dict[str, Any]] = []
        subcommands: list[list[str]] = []
        errors: list[dict[str, Any]] = []
        for function in serialized_functions:
            argv = [analysis_executable, "-q", "-c", f"aa;axtj {hex(function.address)}", str(target)]
            subcommands.append(argv)
            result = self._run_command("function_xrefs", argv, "rizin", env=env)
            if result.status != "completed":
                errors.append(
                    {
                        "function": function.name,
                        "status": result.status,
                        "return_code": result.return_code,
                        "stderr": result.stderr[:400],
                    }
                )
                continue
            payload = self._load_json_payload(result.stdout)
            callers: list[dict[str, Any]] = []
            if isinstance(payload, list):
                for item in payload[:20]:
                    if not isinstance(item, dict):
                        continue
                    from_addr = item.get("from")
                    callers.append(
                        {
                            "from": hex(from_addr) if isinstance(from_addr, int) else from_addr,
                            "type": item.get("type"),
                            "function": item.get("fcn_name"),
                            "opcode": item.get("opcode"),
                            "refname": item.get("refname"),
                        }
                    )
            summaries.append(
                {
                    "name": function.name,
                    "address": hex(function.address),
                    "size": function.size,
                    "reason": function.reason,
                    "caller_count": len(callers),
                    "callers": callers,
                }
            )

        status = "completed" if summaries else "failed"
        payload = {
            "functions": summaries,
            "errors": errors,
        }
        return CommandEvidence(
            command_id="function_xrefs",
            command=[analysis_executable, "--focus-xrefs", str(target)],
            return_code=0 if status == "completed" else 1,
            tool_name="rizin",
            status=status,
            stdout=json.dumps(payload, ensure_ascii=False, indent=2)[: self.settings.tool_output_limit],
            stderr="; ".join(f"{item['function']}={item['status']}" for item in errors[:6])[: self.settings.tool_output_limit],
            metadata={"subcommands": subcommands},
        )

    def _run_gdb_poc_sync(self, target: Path, functions: Any) -> CommandEvidence:
        capability = self._build_capability("gdb_poc")
        executable = capability.executable
        if not capability.available or executable is None:
            return self._unavailable_evidence("gdb_poc", "gdb", capability.summary)
        ensure_target_executable(target)
        if not os.access(target, os.X_OK):
            return CommandEvidence(
                command_id="gdb_poc",
                command=[executable, "--args", str(target)],
                return_code=0,
                tool_name="gdb",
                status="skipped",
                stderr=f"Target is not executable: {target}",
            )

        targets = self._deserialize_issue_targets(functions)
        if not targets:
            return CommandEvidence(
                command_id="gdb_poc",
                command=[executable, "--args", str(target)],
                return_code=0,
                tool_name="gdb",
                status="skipped",
                stderr="No issue-bearing functions selected for GDB PoC validation",
            )

        for issue_target in targets:
            if issue_target.issue_type == "format-string":
                return self._run_format_string_gdb_poc(executable, target, issue_target)
            if issue_target.issue_type == "overflow-candidate":
                return self._run_overflow_gdb_poc(executable, target, issue_target)

        selected = targets[0]
        payload = {
            "validated": False,
            "issue_type": selected.issue_type,
            "function": {
                "name": selected.name,
                "address": hex(selected.address),
            },
            "breakpoint": hex(selected.breakpoint) if selected.breakpoint is not None else None,
            "call_target": selected.call_target,
            "issue_evidence": selected.issue_evidence,
            "summary": f"当前仅对 format-string 原语提供脚本化 GDB PoC，未对 {selected.issue_type} 生成已验证利用载荷。",
            "rce_assessment": self._build_unvalidated_rce_assessment(selected),
        }
        return CommandEvidence(
            command_id="gdb_poc",
            command=[executable, "--args", str(target)],
            return_code=0,
            tool_name="gdb",
            status="completed",
            stdout=json.dumps(payload, ensure_ascii=False, indent=2)[: self.settings.tool_output_limit],
            metadata={"supported_issue_types": ["format-string"]},
        )

    def _run_format_string_gdb_poc(self, executable: str, target: Path, issue_target: IssueTarget) -> CommandEvidence:
        marker = "FMT_PROBE"
        payload = f"{marker}.%p.%p.%p.%p\n"
        breakpoint_address = issue_target.breakpoint or issue_target.address

        with tempfile.TemporaryDirectory(dir=self.settings.runtime_dir) as temp_dir:
            temp_root = Path(temp_dir)
            input_path = temp_root / "fmt_probe.in"
            input_path.write_text(payload, encoding="utf-8")

            gdb_commands = [
                "set pagination off",
                "set confirm off",
                "set debuginfod enabled off",
                f"break *{hex(breakpoint_address)}",
                f"run < {shlex.quote(str(input_path))}",
                "x/i $pc",
                "info registers rdi rsi rdx rcx r8 r9",
                "x/s $rdi",
                "bt",
            ]
            argv = [executable, "-q", "-nx", "-batch"]
            for command in gdb_commands:
                argv.extend(["-ex", command])
            argv.extend(["--args", str(target)])

            gdb_result = self._run_command("gdb_poc", argv, "gdb")
            if gdb_result.status not in {"completed", "failed"}:
                return gdb_result

            gdb_validation = self._validate_format_string_gdb_output(
                gdb_result.stdout,
                marker=marker,
                breakpoint_address=breakpoint_address,
                call_target=issue_target.call_target,
            )
            native_probe = self._run_native_payload_probe(target, payload)
            validated = bool(gdb_validation["validated"]) and bool(native_probe.get("validated"))
            result_payload = {
                "validated": validated,
                "issue_type": issue_target.issue_type,
                "function": {
                    "name": issue_target.name,
                    "address": hex(issue_target.address),
                },
                "breakpoint": hex(breakpoint_address),
                "call_target": issue_target.call_target,
                "call_site": issue_target.call_site,
                "issue_evidence": issue_target.issue_evidence,
                "payload": payload.rstrip("\n"),
                "gdb_commands": gdb_commands,
                "gdb_observation": gdb_validation,
                "native_probe": native_probe,
                "rce_assessment": self._build_format_string_rce_assessment(
                    issue_target=issue_target,
                    gdb_validation=gdb_validation,
                    native_probe=native_probe,
                ),
                "poc": {
                    "command": self._build_python_stdin_poc_command(target, payload),
                    "type": "stdin-leak",
                    "summary": "通过标准输入提交格式串探针并观察程序输出是否展开 `%p`。",
                },
                "exploit_script": self._build_format_string_exploit_script(
                    target=target,
                    payload=payload,
                    breakpoint_address=breakpoint_address,
                    native_probe=native_probe,
                ),
            }
            stderr_parts = [gdb_result.stderr.strip(), str(native_probe.get("stderr") or "").strip()]
            metadata = {
                "subcommands": [
                    argv,
                    [str(target)],
                ],
                "skill_gdb_reference": self.pwn_skill.gdb_reference_excerpt(limit=240),
            }
            return CommandEvidence(
                command_id="gdb_poc",
                command=argv,
                return_code=0 if validated else gdb_result.return_code,
                tool_name="gdb",
                status="completed" if validated or gdb_result.status == "completed" else gdb_result.status,
                stdout=json.dumps(result_payload, ensure_ascii=False, indent=2)[: self.settings.tool_output_limit],
                stderr="\n".join(part for part in stderr_parts if part)[: self.settings.tool_output_limit],
                metadata=metadata,
            )

    def _run_overflow_gdb_poc(self, executable: str, target: Path, issue_target: IssueTarget) -> CommandEvidence:
        breakpoint_address = issue_target.breakpoint or issue_target.address
        probe_length = self._select_overflow_probe_length(issue_target.issue_evidence)
        pattern = self._build_cyclic_pattern(probe_length)
        payload = pattern + b"\n"

        with tempfile.TemporaryDirectory(dir=self.settings.runtime_dir) as temp_dir:
            temp_root = Path(temp_dir)
            input_path = temp_root / "overflow_probe.in"
            input_path.write_bytes(payload)

            gdb_commands = [
                "set pagination off",
                "set confirm off",
                "set debuginfod enabled off",
                "handle SIGALRM nostop noprint pass",
                f"break *{hex(breakpoint_address)}",
                f"run < {shlex.quote(str(input_path))}",
                "x/i $pc",
                "info registers rdi rsi rdx rcx r8 r9 rbp rsp",
                "continue",
                "info program",
                "info registers rip rsp rbp",
                "x/16gx $rsp",
                "bt",
            ]
            argv = [executable, "-q", "-nx", "-batch"]
            for command in gdb_commands:
                argv.extend(["-ex", command])
            argv.extend(["--args", str(target)])

            gdb_result = self._run_command("gdb_poc", argv, "gdb")
            if gdb_result.status not in {"completed", "failed"}:
                return gdb_result

            native_probe = self._run_overflow_native_probe(target, payload)
            gdb_validation = self._validate_overflow_gdb_output(
                gdb_result.stdout,
                pattern=pattern,
                breakpoint_address=breakpoint_address,
                call_target=issue_target.call_target,
                native_probe=native_probe,
            )
            validated = bool(gdb_validation["validated"])
            result_payload = {
                "validated": validated,
                "issue_type": issue_target.issue_type,
                "function": {
                    "name": issue_target.name,
                    "address": hex(issue_target.address),
                },
                "breakpoint": hex(breakpoint_address),
                "call_target": issue_target.call_target,
                "call_site": issue_target.call_site,
                "issue_evidence": issue_target.issue_evidence,
                "payload_length": probe_length,
                "payload_preview": payload[:48].decode("latin-1", errors="replace"),
                "gdb_commands": gdb_commands,
                "gdb_observation": gdb_validation,
                "native_probe": native_probe,
                "rce_assessment": self._build_overflow_rce_assessment(
                    issue_target=issue_target,
                    gdb_validation=gdb_validation,
                    native_probe=native_probe,
                ),
                "poc": {
                    "command": self._build_python_bytes_poc_command(target, payload),
                    "type": "stdin-cyclic",
                    "summary": "通过循环模式输入配合 GDB 观察栈覆盖、崩溃点与 RIP 控制阶段。",
                },
                "exploit_script": self._build_overflow_exploit_script(
                    target=target,
                    payload=payload,
                    breakpoint_address=breakpoint_address,
                    gdb_validation=gdb_validation,
                    native_probe=native_probe,
                ),
            }
            stderr_parts = [gdb_result.stderr.strip(), str(native_probe.get("stderr") or "").strip()]
            metadata = {
                "subcommands": [
                    argv,
                    [str(target)],
                ],
                "skill_gdb_reference": self.pwn_skill.gdb_reference_excerpt(limit=240),
            }
            return CommandEvidence(
                command_id="gdb_poc",
                command=argv,
                return_code=0 if validated else gdb_result.return_code,
                tool_name="gdb",
                status="completed" if validated or gdb_result.status == "completed" else gdb_result.status,
                stdout=json.dumps(result_payload, ensure_ascii=False, indent=2)[: self.settings.tool_output_limit],
                stderr="\n".join(part for part in stderr_parts if part)[: self.settings.tool_output_limit],
                metadata=metadata,
            )

    def _validate_format_string_gdb_output(
        self,
        stdout: str,
        *,
        marker: str,
        breakpoint_address: int,
        call_target: str,
    ) -> dict[str, Any]:
        pc_line = ""
        argument_line = ""
        register_preview: list[str] = []
        backtrace_line = ""
        for raw_line in stdout.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("=>") and not pc_line:
                pc_line = line
                continue
            if line.startswith(("rdi", "rsi", "rdx", "rcx", "r8", "r9")) and len(register_preview) < 6:
                register_preview.append(line)
                continue
            if marker in line and line.startswith("0x") and not argument_line:
                argument_line = line
                continue
            if line.startswith("#0") and not backtrace_line:
                backtrace_line = line

        call_hint = call_target.split("@", 1)[0].lower()
        validated = (
            marker in stdout
            and hex(breakpoint_address) in stdout
            and ("printf" in stdout.lower() or "printf" in call_hint)
            and bool(argument_line)
        )
        return {
            "validated": validated,
            "breakpoint_line": pc_line,
            "argument_line": argument_line,
            "register_preview": register_preview,
            "backtrace_line": backtrace_line,
        }

    def _run_native_payload_probe(self, target: Path, payload: str) -> dict[str, Any]:
        raw_probe = self._run_raw_native_probe(target, payload.encode("utf-8"))
        stdout_full = str(raw_probe.get("stdout_full") or "")
        stderr = str(raw_probe.get("stderr") or "")
        return_code = int(raw_probe.get("return_code", 0) or 0)
        command = [str(target)]
        probe_line = next((line for line in stdout_full.splitlines() if "FMT_PROBE" in line), "")
        marker_index = probe_line.find("FMT_PROBE")
        if marker_index >= 0:
            probe_line = probe_line[marker_index:]
        validated = bool(
            probe_line
            and probe_line.strip() != payload.strip()
            and re.search(r"0x[0-9a-fA-F]{4,}", probe_line)
        )
        return {
            "validated": validated,
            "return_code": return_code,
            "probe_line": probe_line[:240],
            "stdout_preview": stdout_full[:1200].strip(),
            "stderr": stderr.strip(),
            "signal": raw_probe.get("signal"),
            "command": command,
        }

    def _build_python_stdin_poc_command(self, target: Path, payload: str) -> str:
        escaped = payload.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        return (
            "python3 -c 'import sys; sys.stdout.write(\""
            + escaped
            + "\")' | "
            + shlex.quote(str(target))
        )

    def _build_python_bytes_poc_command(self, target: Path, payload: bytes) -> str:
        return (
            "python3 -c 'import sys; sys.stdout.buffer.write("
            + repr(payload)
            + ")' | "
            + shlex.quote(str(target))
        )

    def _build_format_string_exploit_script(
        self,
        target: Path,
        payload: str,
        breakpoint_address: int,
        native_probe: dict[str, Any],
    ) -> dict[str, str]:
        observed_probe_line = str(native_probe.get("probe_line") or "").strip()
        script = "\n".join(
            [
                "#!/usr/bin/env python3",
                "import re",
                "from pwn import *",
                "",
                f"BINARY = {str(target)!r}",
                f"PAYLOAD = {payload.encode('utf-8')!r}",
                "",
                "context.binary = ELF(BINARY, checksec=False)",
                "context.log_level = 'info'",
                "",
                "def main():",
                "    io = process(context.binary.path)",
                "    banner = io.recvline(timeout=1) or b''",
                "    if banner:",
                "        log.info('banner=%r', banner.rstrip())",
                "    io.send(PAYLOAD)",
                "    output = io.recvall(timeout=2)",
                "    print(output.decode('latin-1', errors='replace'))",
                "    probe_line = next((line for line in output.splitlines() if b'FMT_PROBE.' in line), b'')",
                "    assert probe_line, 'format string marker not observed'",
                "    assert re.search(rb'0x[0-9a-fA-F]{4,}', probe_line), 'expected pointer leak not observed'",
                "    log.info('exploit_stage=info-leak; rce=false; getshell=false')",
                "",
                "if __name__ == '__main__':",
                "    main()",
            ]
        )
        expected = observed_probe_line or str(native_probe.get("stdout_preview") or "").strip()
        return {
            "language": "python",
            "filename": "exploit_fmt_probe.py",
            "summary": "基于真实运行结果验证格式化字符串信息泄露原语的最小 pwntools 脚本。",
            "content": script,
            "expected_output": expected,
        }

    def _build_format_string_rce_assessment(
        self,
        *,
        issue_target: IssueTarget,
        gdb_validation: dict[str, Any],
        native_probe: dict[str, Any],
    ) -> dict[str, Any]:
        validated = bool(gdb_validation.get("validated")) and bool(native_probe.get("validated"))
        if validated:
            verdict = (
                f"{issue_target.name} 的动态调试已证明格式串实参可控，并在真实运行中观察到地址泄露。"
                "当前证据只到信息泄露阶段，未观察到写原语、控制流劫持、命令执行或 getshell。"
            )
            stage_id = "info-leak"
            stage_label = "已验证信息泄露，未到 RCE / getshell"
        else:
            verdict = (
                f"{issue_target.name} 当前仅有格式串怀疑点，动态调试未同时满足 GDB 与原生输出两条验证链，"
                "不能把结论推进到信息泄露或 RCE。"
            )
            stage_id = "not-validated"
            stage_label = "未验证到可利用阶段"
        return {
            "stage_id": stage_id,
            "stage_label": stage_label,
            "rce_reached": False,
            "getshell_reached": False,
            "verdict": verdict,
            "boundary": "未观察到写原语、控制流劫持、命令执行或 shell 交互。",
            "dynamic_evidence": [
                line
                for line in (
                    self._compact_text(gdb_validation.get("breakpoint_line")),
                    self._compact_text(gdb_validation.get("argument_line")),
                    self._compact_text(native_probe.get("probe_line")),
                )
                if line
            ],
        }

    def _build_unvalidated_rce_assessment(self, issue_target: IssueTarget) -> dict[str, Any]:
        return {
            "stage_id": "not-validated",
            "stage_label": "未验证到可利用阶段",
            "rce_reached": False,
            "getshell_reached": False,
            "verdict": (
                f"{issue_target.name} 当前只收集到 {issue_target.issue_type} 的静态迹象，"
                "尚未通过动态调试把结论推进到 RCE / getshell。"
            ),
            "boundary": "当前没有 GDB 断点命中、寄存器快照或真实运行输出可证明 exploit stage。",
            "dynamic_evidence": [],
        }

    def _select_overflow_probe_length(self, issue_evidence: str) -> int:
        length = self._extract_issue_size(issue_evidence, "length")
        capacity = self._extract_issue_size(issue_evidence, "capacity")
        if length is not None and capacity is not None:
            return max(capacity + 0x40, min(length, max(capacity + 0x40, 0x120)))
        if length is not None:
            return min(max(length, 0x100), 0x400)
        if capacity is not None:
            return min(max(capacity + 0x60, 0x120), 0x400)
        return 0x180

    def _extract_issue_size(self, issue_evidence: str, field_name: str) -> int | None:
        pattern = rf"{re.escape(field_name)}(?:≈|=)(0x[0-9a-fA-F]+|\d+)"
        match = re.search(pattern, issue_evidence or "")
        if not match:
            return None
        text = match.group(1)
        return int(text, 16 if text.startswith("0x") else 10)

    def _build_cyclic_pattern(self, length: int) -> bytes:
        alphabet_a = b"abcdefghijklmnopqrstuvwxyz"
        alphabet_b = b"ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        alphabet_c = b"0123456789"
        pattern = bytearray()
        for first in alphabet_a:
            for second in alphabet_b:
                for third in alphabet_c:
                    pattern.extend((first, second, third))
                    if len(pattern) >= length:
                        return bytes(pattern[:length])
        return bytes(pattern[:length])

    def _cyclic_find(self, pattern: bytes, value_text: str) -> int | None:
        try:
            value = int(value_text, 16)
        except (TypeError, ValueError):
            return None
        for width in (8, 4):
            try:
                probe = value.to_bytes(width, "little", signed=False)
            except OverflowError:
                continue
            offset = pattern.find(probe)
            if offset >= 0:
                return offset
        return None

    def _run_raw_native_probe(self, target: Path, payload: bytes) -> dict[str, Any]:
        command = [str(target)]
        try:
            completed = subprocess.run(
                command,
                input=payload,
                capture_output=True,
                timeout=min(self.settings.tool_timeout_seconds, 6),
                check=False,
            )
        except subprocess.TimeoutExpired:
            return {
                "return_code": 124,
                "stdout_full": "",
                "stdout_preview": "",
                "stderr": "native payload probe timed out",
                "signal": None,
                "command": command,
            }

        stdout_full = completed.stdout.decode("utf-8", errors="replace")
        signal_name = None
        if completed.returncode < 0:
            signal_name = f"SIG{-completed.returncode}"
        return {
            "return_code": completed.returncode,
            "stdout_full": stdout_full,
            "stdout_preview": stdout_full[:1200].strip(),
            "stderr": completed.stderr.decode("utf-8", errors="replace")[:600].strip(),
            "signal": signal_name,
            "command": command,
        }

    def _run_overflow_native_probe(self, target: Path, payload: bytes) -> dict[str, Any]:
        raw_probe = self._run_raw_native_probe(target, payload)
        return {
            "validated": bool(raw_probe.get("signal")),
            "return_code": raw_probe.get("return_code", 0),
            "stdout_preview": raw_probe.get("stdout_preview", ""),
            "stderr": raw_probe.get("stderr", ""),
            "signal": raw_probe.get("signal"),
            "command": raw_probe.get("command"),
        }

    def _validate_overflow_gdb_output(
        self,
        stdout: str,
        *,
        pattern: bytes,
        breakpoint_address: int,
        call_target: str,
        native_probe: dict[str, Any],
    ) -> dict[str, Any]:
        pc_line = ""
        register_preview: list[str] = []
        signal_line = ""
        rip_line = ""
        rsp_line = ""
        rbp_line = ""
        stack_preview: list[str] = []
        backtrace_line = ""
        signal_seen = False

        for raw_line in stdout.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("=>") and not pc_line:
                pc_line = line
                continue
            if not signal_seen and line.startswith(("rdi", "rsi", "rdx", "rcx", "r8", "r9", "rbp", "rsp")):
                if len(register_preview) < 8:
                    register_preview.append(line)
                continue
            if ("Program received signal" in line or "SIGSEGV" in line or "SIGABRT" in line) and not signal_line:
                signal_line = line
                signal_seen = True
                continue
            if signal_seen and line.startswith("rip") and not rip_line:
                rip_line = line
                continue
            if signal_seen and line.startswith("rsp") and not rsp_line:
                rsp_line = line
                continue
            if signal_seen and line.startswith("rbp") and not rbp_line:
                rbp_line = line
                continue
            if signal_seen and line.startswith("0x") and len(stack_preview) < 6:
                stack_preview.append(line)
                continue
            if line.startswith("#0") and not backtrace_line:
                backtrace_line = line

        rip_value = self._extract_hex_from_text(rip_line)
        rbp_value = self._extract_hex_from_text(rbp_line)
        control_offset = self._cyclic_find(pattern, rip_value) if rip_value else None
        frame_offset = self._cyclic_find(pattern, rbp_value) if rbp_value else None
        stack_offsets: list[dict[str, Any]] = []
        for line in stack_preview:
            values = re.findall(r"0x[0-9a-fA-F]+", line)
            for value_text in values[1:]:
                offset = self._cyclic_find(pattern, value_text)
                if offset is not None:
                    stack_offsets.append({"value": value_text, "offset": offset})
                    break

        stage_id = "not-validated"
        stage_label = "未验证到可利用阶段"
        if control_offset is not None:
            stage_id = "control-hijack"
            stage_label = "已验证返回地址可控，未到 getshell"
        elif frame_offset is not None or stack_offsets:
            stage_id = "stack-overwrite"
            stage_label = "已验证栈帧覆盖，尚未证明 RIP 可控"
        elif signal_line or native_probe.get("signal"):
            stage_id = "crash-only"
            stage_label = "已验证可触发崩溃，尚未证明控制流劫持"

        return {
            "validated": stage_id != "not-validated",
            "stage_id": stage_id,
            "stage_label": stage_label,
            "breakpoint_line": pc_line,
            "register_preview": register_preview,
            "signal_line": signal_line,
            "rip_line": rip_line,
            "rsp_line": rsp_line,
            "rbp_line": rbp_line,
            "stack_preview": stack_preview,
            "backtrace_line": backtrace_line,
            "control_offset": control_offset,
            "frame_offset": frame_offset,
            "stack_offsets": stack_offsets,
            "call_hint": call_target.split("@", 1)[0].lower(),
            "breakpoint_address": hex(breakpoint_address),
        }

    def _build_overflow_rce_assessment(
        self,
        *,
        issue_target: IssueTarget,
        gdb_validation: dict[str, Any],
        native_probe: dict[str, Any],
    ) -> dict[str, Any]:
        stage_id = str(gdb_validation.get("stage_id") or "not-validated")
        if stage_id == "control-hijack":
            stage_label = "已验证返回地址可控，已到控制流劫持阶段，未到 RCE / getshell"
            verdict = (
                f"{issue_target.name} 的动态调试已把溢出结论推进到 RIP 可控。"
                f"当前从循环模式中反推出偏移 {gdb_validation.get('control_offset')}，"
                "说明漏洞不再停留在崩溃层面，但尚未观测到命令执行或 shell 交互。"
            )
            boundary = "当前没有执行到 system/execve，也没有观察到 shell 提示或命令回显。"
        elif stage_id == "stack-overwrite":
            stage_label = "已验证栈帧覆盖，尚未证明 RIP 可控"
            verdict = (
                f"{issue_target.name} 的动态调试已经看到循环模式进入栈帧，"
                "说明输入越界可真实落到栈覆盖，但当前还不能声明控制流已被劫持。"
            )
            boundary = "尚未在 RIP 上定位到循环模式，因此还不能把结论推进到 RCE。"
        elif stage_id == "crash-only":
            stage_label = "已验证崩溃，尚未证明控制流劫持"
            verdict = (
                f"{issue_target.name} 的原生运行或 GDB 调试已触发异常退出，"
                "但当前只证明越界可导致崩溃，不能据此直接认定 RCE / getshell。"
            )
            boundary = "尚未看到栈帧覆盖或 RIP 控制证据。"
        else:
            stage_label = "未验证到可利用阶段"
            verdict = (
                f"{issue_target.name} 目前只有静态溢出迹象，动态调试没有拿到稳定崩溃、栈覆盖或 RIP 控制证据。"
            )
            boundary = "当前不能把结论推进到控制流劫持、RCE 或 getshell。"
        return {
            "stage_id": stage_id,
            "stage_label": stage_label,
            "rce_reached": False,
            "getshell_reached": False,
            "verdict": verdict,
            "boundary": boundary,
            "dynamic_evidence": [
                line
                for line in (
                    self._compact_text(gdb_validation.get("signal_line")),
                    self._compact_text(gdb_validation.get("rip_line")),
                    self._compact_text(native_probe.get("signal")),
                )
                if line
            ],
        }

    def _build_overflow_exploit_script(
        self,
        *,
        target: Path,
        payload: bytes,
        breakpoint_address: int,
        gdb_validation: dict[str, Any],
        native_probe: dict[str, Any],
    ) -> dict[str, str]:
        control_offset = gdb_validation.get("control_offset")
        expected_signal = str(native_probe.get("signal") or gdb_validation.get("signal_line") or "").strip()
        script = "\n".join(
            [
                "#!/usr/bin/env python3",
                "from pwn import *",
                "",
                f"BINARY = {str(target)!r}",
                f"PAYLOAD = {payload!r}",
                "",
                "context.binary = ELF(BINARY, checksec=False)",
                "context.log_level = 'info'",
                "",
                "def main():",
                "    io = process(context.binary.path)",
                "    io.send(PAYLOAD)",
                "    output = io.recvall(timeout=2)",
                "    if output:",
                "        print(output.decode('latin-1', errors='replace'))",
                "    assert io.poll() is not None, 'process should exit or crash after overflow probe'",
                f"    log.info('expected_stage={gdb_validation.get('stage_id', 'not-validated')}')",
                (
                    f"    log.info('control_offset={control_offset}')"
                    if control_offset is not None
                    else "    log.info('control_offset=unconfirmed')"
                ),
                "    log.info('rce=false; getshell=false')",
                "",
                "if __name__ == '__main__':",
                "    main()",
            ]
        )
        return {
            "language": "python",
            "filename": "exploit_overflow_probe.py",
            "summary": "基于真实 GDB 调试验证溢出阶段的最小 pwntools 脚本。",
            "content": script,
            "expected_output": expected_signal,
        }

    def _extract_hex_from_text(self, text: str) -> str:
        match = re.search(r"(0x[0-9a-fA-F]+)", text or "")
        return match.group(1) if match else ""

    def _compact_text(self, value: Any) -> str:
        if value is None:
            return ""
        return re.sub(r"\s+", " ", str(value)).strip()

    async def _run_gdb(self, target: Path) -> CommandEvidence:
        capability = self._build_capability("gdb_batch")
        executable = capability.executable
        if not capability.available or executable is None:
            return self._unavailable_evidence("gdb_batch", "gdb", capability.summary)
        argv = [
            executable,
            "-q",
            "-nx",
            "-batch",
            "-ex",
            "set pagination off",
            "-ex",
            f"file {target}",
            "-ex",
            "info files",
            "-ex",
            "maintenance info sections",
        ]
        return await asyncio.to_thread(self._run_command, "gdb_batch", argv, "gdb")

    async def _run_afl_probe(self, target: Path) -> CommandEvidence:
        capability = self._build_capability("afl_showmap_probe")
        executable = capability.executable
        if not capability.available or executable is None:
            return self._unavailable_evidence("afl_showmap_probe", "afl++", capability.summary)
        ensure_target_executable(target)
        if not os.access(target, os.X_OK):
            return CommandEvidence(
                command_id="afl_showmap_probe",
                command=[executable, "--", str(target)],
                return_code=0,
                tool_name="afl++",
                status="skipped",
                stderr=f"Target is not executable: {target}",
            )

        return await asyncio.to_thread(self._run_afl_probe_sync, executable, target)

    def _run_afl_probe_sync(self, executable: str, target: Path) -> CommandEvidence:
        with tempfile.TemporaryDirectory(dir=self.settings.runtime_dir) as temp_dir:
            out_path = Path(temp_dir) / "afl.map"
            argv = [
                executable,
                "-q",
                "-m",
                "none",
                "-t",
                "2000",
                "-o",
                str(out_path),
                "--",
                str(target),
            ]
            completed = subprocess.run(
                argv,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=min(self.settings.tool_timeout_seconds, 8),
                check=False,
            )
            map_size = out_path.stat().st_size if out_path.exists() else 0
            stdout = (completed.stdout + f"\nmap_size_bytes={map_size}\n")[: self.settings.tool_output_limit]
            stderr = completed.stderr[: self.settings.tool_output_limit]
            status = "completed" if completed.returncode == 0 else "failed"
            return CommandEvidence(
                command_id="afl_showmap_probe",
                command=argv,
                return_code=completed.returncode,
                tool_name="afl++",
                status=status,
                stdout=stdout,
                stderr=stderr,
                metadata={"map_size_bytes": map_size},
            )

    async def _run_angr_cfg(self, target: Path) -> CommandEvidence:
        capability = self._build_capability("angr_cfg")
        if not capability.available:
            return self._unavailable_evidence("angr_cfg", "angr", capability.summary)

        try:
            return await asyncio.wait_for(
                asyncio.to_thread(self._run_angr_cfg_sync, target),
                timeout=self.settings.tool_timeout_seconds,
            )
        except asyncio.TimeoutError:
            return CommandEvidence(
                command_id="angr_cfg",
                command=[sys.executable, "angr::CFGFast", str(target)],
                return_code=124,
                tool_name="angr",
                status="timeout",
                stderr="angr analysis timed out",
            )

    def _run_angr_cfg_sync(self, target: Path) -> CommandEvidence:
        import angr  # type: ignore

        try:
            project = angr.Project(str(target), auto_load_libs=False)
            cfg = project.analyses.CFGFast(normalize=True)
            main_object = project.loader.main_object
            functions = [
                {
                    "addr": hex(function.addr),
                    "name": function.name,
                    "size": function.size,
                }
                for function in list(cfg.kb.functions.values())[:80]
            ]
            segments = []
            for index, segment in enumerate(main_object.segments):
                segment_name = getattr(segment, "segment_name", None) or getattr(segment, "name", None) or f"segment_{index}"
                segments.append(
                    {
                        "name": str(segment_name),
                        "min_addr": hex(segment.min_addr),
                        "max_addr": hex(segment.max_addr),
                        "offset": hex(getattr(segment, "offset", 0)),
                        "flags": getattr(segment, "flags", None),
                        "readable": bool(getattr(segment, "is_readable", False)),
                        "writable": bool(getattr(segment, "is_writable", False)),
                        "executable": bool(getattr(segment, "is_executable", False)),
                    }
                )
                if index + 1 >= 40:
                    break

            payload = {
                "arch": getattr(project.arch, "name", "unknown"),
                "entry": hex(project.entry),
                "imports": sorted(list(main_object.imports.keys()))[:80],
                "segments": segments,
                "functions": functions,
            }
            return CommandEvidence(
                command_id="angr_cfg",
                command=[sys.executable, "angr::CFGFast", str(target)],
                return_code=0,
                tool_name="angr",
                status="completed",
                stdout=json.dumps(payload, ensure_ascii=False, indent=2)[: self.settings.tool_output_limit],
            )
        except Exception as exc:
            return CommandEvidence(
                command_id="angr_cfg",
                command=[sys.executable, "angr::CFGFast", str(target)],
                return_code=1,
                tool_name="angr",
                status="failed",
                stderr=f"angr analysis failed: {exc}",
                metadata={"exception_type": type(exc).__name__},
            )

    async def _run_ida_batch(self, target: Path) -> CommandEvidence:
        capability = self._build_capability("ida_batch")
        executable = capability.executable
        if not capability.available or executable is None:
            return self._unavailable_evidence("ida_batch", "ida", capability.summary)
        return await asyncio.to_thread(self._run_ida_batch_sync, executable, target)

    def _run_ida_batch_sync(self, executable: str, target: Path) -> CommandEvidence:
        exporter_script = self._resolve_rootfs_elf_exporter_script()
        rootfs_result: CommandEvidence | None = None
        if exporter_script is not None:
            rootfs_result = self._run_rootfs_elf_ida_sync(executable, exporter_script, target)
            if rootfs_result.status == "completed":
                return rootfs_result

        builtin_result = self._run_builtin_ida_batch_sync(executable, target)
        if rootfs_result is not None and rootfs_result.status != "completed":
            fallback_note = f"rootfs_elf exporter failed, fell back to builtin IDA: {rootfs_result.stderr}".strip()
            builtin_result.stderr = (
                f"{fallback_note}\n\n{builtin_result.stderr}".strip()
                if builtin_result.stderr
                else fallback_note
            )
            fallbacks = list(builtin_result.metadata.get("fallbacks", []))
            fallbacks.append(
                {
                    "exporter": "rootfs_elf",
                    "status": rootfs_result.status,
                    "reason": rootfs_result.stderr[:300],
                }
            )
            builtin_result.metadata["fallbacks"] = fallbacks
        return builtin_result

    def _run_rootfs_elf_ida_sync(self, executable: str, exporter_script: Path, target: Path) -> CommandEvidence:
        ida_dir = self._resolve_ida_install_dir(executable)
        if ida_dir is None:
            return CommandEvidence(
                command_id="ida_batch",
                command=[sys.executable, str(exporter_script), "--elf", str(target)],
                return_code=1,
                tool_name="ida",
                status="failed",
                stderr="rootfs_elf exporter requires an IDA install root with idalib/python",
                metadata={"exporter": "rootfs_elf"},
            )

        with tempfile.TemporaryDirectory(dir=self.settings.runtime_dir) as temp_dir:
            temp_dir_path = Path(temp_dir)
            output_dir = temp_dir_path / "ida_export"
            log_path = temp_dir_path / "ida.log"
            argv = [
                sys.executable,
                str(exporter_script),
                "--elf",
                str(target),
                "--out-dir",
                str(output_dir),
                "--ida-dir",
                ida_dir,
                "--skip-memory",
                "--no-decompile-funcs",
                "--log-path",
                str(log_path),
            ]
            env = os.environ.copy()
            env["IDADIR"] = ida_dir
            completed = subprocess.run(
                argv,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=max(self.settings.tool_timeout_seconds, 90),
                check=False,
                env=env,
            )
            has_primary_artifacts = (output_dir / "source.c").exists() and (output_dir / "imports.txt").exists()
            status = "completed" if completed.returncode == 0 and has_primary_artifacts else "failed"
            stdout, metadata = self._summarize_rootfs_elf_ida_output(output_dir, target, ida_dir)
            stderr_parts = [completed.stderr]
            if log_path.exists():
                stderr_parts.append(log_path.read_text(encoding="utf-8", errors="replace"))
            stderr = "\n".join(part for part in stderr_parts if part).strip()
            return CommandEvidence(
                command_id="ida_batch",
                command=argv,
                return_code=completed.returncode,
                tool_name="ida",
                status=status,
                stdout=stdout[: self.settings.tool_output_limit],
                stderr=stderr[: self.settings.tool_output_limit],
                metadata=metadata,
            )

    def _run_builtin_ida_batch_sync(self, executable: str, target: Path) -> CommandEvidence:
        with tempfile.TemporaryDirectory(dir=self.settings.runtime_dir) as temp_dir:
            temp_dir_path = Path(temp_dir)
            analysis_target = temp_dir_path / target.name
            shutil.copy2(target, analysis_target)
            script_path = temp_dir_path / "ida_export.py"
            output_path = temp_dir_path / "ida.json"
            log_path = temp_dir_path / "ida.log"
            script_path.write_text(self._ida_script, encoding="utf-8")

            argv = [
                executable,
                "-A",
                f"-L{log_path}",
                f"-S{script_path}",
                str(analysis_target),
            ]
            env = os.environ.copy()
            env["IDA_JSON_OUT"] = str(output_path)
            completed = subprocess.run(
                argv,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=max(self.settings.tool_timeout_seconds, 60),
                check=False,
                env=env,
            )
            status = "completed" if completed.returncode == 0 and output_path.exists() else "failed"
            stdout = output_path.read_text(encoding="utf-8") if output_path.exists() else completed.stdout
            stderr_parts = [completed.stderr]
            if log_path.exists():
                stderr_parts.append(log_path.read_text(encoding="utf-8", errors="replace"))
            stderr = "\n".join(part for part in stderr_parts if part).strip()
            return CommandEvidence(
                command_id="ida_batch",
                command=argv,
                return_code=completed.returncode,
                tool_name="ida",
                status=status,
                stdout=stdout[: self.settings.tool_output_limit],
                stderr=stderr[: self.settings.tool_output_limit],
                metadata={"exporter": "builtin"},
            )

    def _build_capability(self, tool_id: str) -> ToolCapability:
        descriptor = self.TOOL_DESCRIPTORS[tool_id]
        enabled = self.is_tool_enabled(tool_id)

        if descriptor.mode == "python":
            available = importlib.util.find_spec(descriptor.family) is not None
            return ToolCapability(
                tool_id=tool_id,
                family=descriptor.family,
                available=available,
                enabled=enabled,
                mode=descriptor.mode,
                summary=(
                    descriptor.summary
                    if available and enabled
                    else (
                        f"{descriptor.summary}（当前已关闭）"
                        if available
                        else f"Python module `{descriptor.family}` is not installed"
                    )
                ),
            )

        if descriptor.mode == "ida":
            executable = self._resolve_ida_binary()
            exporter_script = self._resolve_rootfs_elf_exporter_script()
            metadata = {"exporter": "rootfs_elf" if exporter_script else "builtin"}
            if exporter_script is not None:
                metadata["exporter_script"] = str(exporter_script)
            return ToolCapability(
                tool_id=tool_id,
                family=descriptor.family,
                available=executable is not None,
                enabled=enabled,
                executable=executable,
                mode=descriptor.mode,
                summary=(
                    descriptor.summary
                    if executable and enabled
                    else (
                        f"{descriptor.summary}（当前已关闭）"
                        if executable
                        else "Headless IDA executable not found"
                    )
                ),
                metadata=metadata,
            )

        executable = self._resolve_executable(descriptor.candidates)
        return ToolCapability(
            tool_id=tool_id,
            family=descriptor.family,
            available=executable is not None,
            enabled=enabled,
            executable=executable,
            mode=descriptor.mode,
            summary=(
                descriptor.summary
                if executable and enabled
                else (
                    f"{descriptor.summary}（当前已关闭）"
                    if executable
                    else f"Executable not found: {', '.join(descriptor.candidates)}"
                )
            ),
        )

    def _resolve_executable(self, candidates: tuple[str, ...]) -> str | None:
        for candidate in candidates:
            resolved = self._resolve_named_executable(candidate)
            if resolved is not None:
                return resolved
        return None

    def _resolve_named_executable(self, candidate: str) -> str | None:
        for directory in self._local_tool_bin_dirs():
            local_path = directory / candidate
            if local_path.exists() and os.access(local_path, os.X_OK):
                return str(local_path)
        return shutil.which(candidate)

    def _local_tool_bin_dirs(self) -> list[Path]:
        vendor_radare2_bin = self.settings.host_workspace_dir / ".vendor" / "radare2" / "root" / "usr" / "bin"
        return [vendor_radare2_bin] if vendor_radare2_bin.exists() else []

    def _build_command_env(self, executable: str | None) -> dict[str, str] | None:
        if executable is None:
            return None
        vendor_root = self.settings.host_workspace_dir / ".vendor" / "radare2" / "root"
        executable_path = Path(executable).resolve()
        try:
            executable_path.relative_to(vendor_root)
        except ValueError:
            return None

        env = os.environ.copy()
        library_dir = vendor_root / "usr" / "lib" / "x86_64-linux-gnu"
        if library_dir.exists():
            current = env.get("LD_LIBRARY_PATH", "")
            env["LD_LIBRARY_PATH"] = f"{library_dir}:{current}" if current else str(library_dir)
        return env

    def _resolve_rizin_binaries(self) -> dict[str, str]:
        resolved: dict[str, str] = {}
        for candidate in self.TOOL_DESCRIPTORS["rizin_overview"].candidates:
            executable = self._resolve_named_executable(candidate)
            if executable is not None:
                resolved[candidate] = executable
        return resolved

    def _load_json_payload(self, text: str):
        cleaned = text.replace("\x1b[2K\r", "").strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return None

    def _normalize_import_name(self, name: str) -> str:
        return name.split("@", 1)[0].strip()

    def _serialize_focus_function(self, function: FocusFunction) -> dict[str, Any]:
        return {
            "name": function.name,
            "address": function.address,
            "size": function.size,
            "reason": function.reason,
        }

    def _deserialize_focus_functions(self, items: Any) -> list[FocusFunction]:
        functions: list[FocusFunction] = []
        if not isinstance(items, list):
            return functions
        for item in items:
            if not isinstance(item, dict):
                continue
            address = item.get("address")
            if not isinstance(address, int):
                continue
            size = item.get("size")
            functions.append(
                FocusFunction(
                    name=str(item.get("name") or hex(address)),
                    address=address,
                    size=int(size) if isinstance(size, int) and size > 0 else None,
                    reason=str(item.get("reason") or ""),
                )
            )
        return functions

    def _deserialize_issue_targets(self, items: Any) -> list[IssueTarget]:
        targets: list[IssueTarget] = []
        if not isinstance(items, list):
            return targets
        for item in items:
            if not isinstance(item, dict):
                continue
            address = item.get("address")
            if not isinstance(address, int) or address <= 0:
                continue
            breakpoint_value = item.get("breakpoint")
            breakpoint_address = breakpoint_value if isinstance(breakpoint_value, int) and breakpoint_value > 0 else None
            size = item.get("size")
            targets.append(
                IssueTarget(
                    name=str(item.get("name") or hex(address)),
                    address=address,
                    issue_type=str(item.get("issue_type") or "").strip(),
                    breakpoint=breakpoint_address,
                    size=int(size) if isinstance(size, int) and size > 0 else None,
                    reason=str(item.get("reason") or ""),
                    issue_evidence=str(item.get("issue_evidence") or ""),
                    call_target=str(item.get("call_target") or ""),
                    call_site=str(item.get("call_site") or ""),
                )
            )
        return [item for item in targets if item.issue_type]

    def _normalize_function_key(self, name: str, address: int) -> tuple[str, int]:
        return (name.strip().lower(), address)

    def _parse_address_int(self, value: Any) -> int | None:
        if isinstance(value, int):
            return value if value > 0 else None
        text = str(value or "").strip()
        if not text:
            return None
        try:
            return int(text, 16 if text.lower().startswith("0x") else 10)
        except ValueError:
            return None

    def _extract_follow_up_function_keys(
        self,
        evidence: list[CommandEvidence],
        command_id: str,
    ) -> set[tuple[str, int]]:
        keys: set[tuple[str, int]] = set()
        for item in evidence:
            if item.command_id != command_id or item.status != "completed":
                continue
            payload = self._load_json_payload(item.stdout)
            if not isinstance(payload, dict):
                continue
            for function in payload.get("functions", []) or []:
                if not isinstance(function, dict):
                    continue
                address = self._parse_address_int(function.get("address"))
                if address is None:
                    continue
                name = str(function.get("name") or hex(address))
                keys.add(self._normalize_function_key(name, address))
        return keys

    def _filter_uncovered_focus_functions(
        self,
        focus_functions: list[FocusFunction],
        existing_keys: set[tuple[str, int]],
    ) -> list[FocusFunction]:
        pending: list[FocusFunction] = []
        for function in focus_functions:
            key = self._normalize_function_key(function.name, function.address)
            if key in existing_keys:
                continue
            pending.append(function)
        return pending

    def _extract_existing_gdb_poc_keys(self, evidence: list[CommandEvidence]) -> set[tuple[str, int, str]]:
        keys: set[tuple[str, int, str]] = set()
        for item in evidence:
            if item.command_id != "gdb_poc" or item.status != "completed":
                continue
            payload = self._load_json_payload(item.stdout)
            if not isinstance(payload, dict):
                continue
            function = payload.get("function") or {}
            if not isinstance(function, dict):
                continue
            address = self._parse_address_int(function.get("address"))
            issue_type = str(payload.get("issue_type") or "").strip()
            if address is None or not issue_type:
                continue
            name = str(function.get("name") or hex(address))
            keys.add((name.strip().lower(), address, issue_type))
        return keys

    def _filter_issue_targets_missing_poc(
        self,
        evidence: list[CommandEvidence],
        issue_targets: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        existing_keys = self._extract_existing_gdb_poc_keys(evidence)
        pending: list[dict[str, Any]] = []
        for item in issue_targets:
            if not isinstance(item, dict):
                continue
            address = self._parse_address_int(item.get("address"))
            issue_type = str(item.get("issue_type") or "").strip()
            if address is None or not issue_type:
                continue
            name = str(item.get("name") or hex(address))
            key = (name.strip().lower(), address, issue_type)
            if key in existing_keys:
                continue
            pending.append(item)
        return pending

    def _identify_focus_functions(
        self,
        evidence: list[CommandEvidence],
        peer_notes: list[str] | None = None,
    ) -> list[FocusFunction]:
        candidates: dict[str, FocusFunction] = {}
        scores: dict[str, int] = {}
        xref_callers = self._extract_dangerous_xref_callers(evidence)
        symbol_functions = self._extract_defined_functions(evidence)
        angr_functions = self._extract_angr_functions(evidence)
        ida_functions = self._extract_ida_functions(evidence)
        rizin_functions = self._extract_rizin_functions(evidence)
        peer_functions = self._extract_peer_focus_functions(peer_notes or [])

        for function in symbol_functions + angr_functions + ida_functions + rizin_functions + peer_functions:
            if function.address <= 0:
                continue
            key = f"{function.name}@{function.address:x}"
            existing = candidates.get(key)
            if existing is None or (existing.size is None and function.size is not None):
                candidates[key] = function
            scores.setdefault(key, 0)
            scores[key] += 4

            normalized_name = function.name.lower()
            if normalized_name in xref_callers:
                scores[key] += 8
                candidates[key] = FocusFunction(
                    name=function.name,
                    address=function.address,
                    size=function.size,
                    reason="calls-dangerous-import",
                )
            if normalized_name in {"main", "get_info", "my_gadget", "vuln", "win"}:
                scores[key] += 6
            if any(token in normalized_name for token in ("input", "read", "parse", "menu", "welcome", "check", "handle", "gadget")):
                scores[key] += 3
            if normalized_name.startswith("sym.imp.") or "@plt" in normalized_name:
                scores[key] -= 10
            if normalized_name in {"_start", "_init", "_fini", "frame_dummy", "register_tm_clones", "deregister_tm_clones"}:
                scores[key] -= 8

        ranked = sorted(
            candidates.values(),
            key=lambda item: (
                scores.get(f"{item.name}@{item.address:x}", 0),
                -(item.size or 0),
                item.address,
            ),
            reverse=True,
        )
        deduped: list[FocusFunction] = []
        seen_addresses: set[int] = set()
        for item in ranked:
            if item.address in seen_addresses:
                continue
            seen_addresses.add(item.address)
            deduped.append(item)
            if len(deduped) >= 4:
                break
        return deduped

    def _extract_peer_focus_functions(self, peer_notes: list[str]) -> list[FocusFunction]:
        functions: list[FocusFunction] = []
        seen: set[tuple[str, int]] = set()
        for note in peer_notes:
            if not note:
                continue
            for match in re.finditer(r"([A-Za-z_][A-Za-z0-9_.$@-]{1,63})\s*@\s*(0x[0-9a-fA-F]+)", note):
                name = match.group(1)
                try:
                    address = int(match.group(2), 16)
                except ValueError:
                    continue
                key = (name, address)
                if key in seen:
                    continue
                seen.add(key)
                functions.append(
                    FocusFunction(
                        name=name,
                        address=address,
                        reason="peer-coordination",
                    )
                )
        return functions

    def _extract_issue_targets(self, evidence: list[CommandEvidence]) -> list[dict[str, Any]]:
        issue_targets: list[IssueTarget] = []
        seen: set[tuple[str, int, str, int | None]] = set()

        for item in evidence:
            if item.command_id != "function_disasm" or item.status != "completed":
                continue
            payload = self._load_json_payload(item.stdout)
            if not isinstance(payload, dict):
                continue
            for function in payload.get("functions", []) or []:
                if not isinstance(function, dict):
                    continue
                try:
                    function_address = int(str(function.get("address")), 16)
                except (TypeError, ValueError):
                    continue
                function_name = str(function.get("name") or hex(function_address))
                function_size = function.get("size")
                for call_site in function.get("call_sites", []) or []:
                    if not isinstance(call_site, dict):
                        continue
                    issue = call_site.get("issue")
                    if not isinstance(issue, dict):
                        continue
                    issue_type = str(issue.get("type") or "").strip()
                    if not issue_type:
                        continue
                    breakpoint_text = str(call_site.get("from") or "")
                    try:
                        breakpoint_address = int(breakpoint_text, 16)
                    except ValueError:
                        breakpoint_address = None
                    key = (function_name, function_address, issue_type, breakpoint_address)
                    if key in seen:
                        continue
                    seen.add(key)
                    issue_targets.append(
                        IssueTarget(
                            name=function_name,
                            address=function_address,
                            issue_type=issue_type,
                            breakpoint=breakpoint_address,
                            size=int(function_size) if isinstance(function_size, int) and function_size > 0 else None,
                            reason=str(function.get("reason") or issue_type),
                            issue_evidence=str(issue.get("evidence") or ""),
                            call_target=str(call_site.get("target") or ""),
                            call_site=breakpoint_text,
                        )
                    )

        priority = {
            "format-string": 0,
            "overflow-candidate": 1,
        }
        ranked = sorted(
            issue_targets,
            key=lambda item: (
                priority.get(item.issue_type, 9),
                0 if item.breakpoint is not None else 1,
                item.address,
                item.name,
            ),
        )
        return [
            {
                "name": item.name,
                "address": item.address,
                "size": item.size,
                "reason": item.reason,
                "issue_type": item.issue_type,
                "issue_evidence": item.issue_evidence,
                "call_target": item.call_target,
                "call_site": item.call_site,
                "breakpoint": item.breakpoint,
            }
            for item in ranked
        ]

    def _extract_defined_functions(self, evidence: list[CommandEvidence]) -> list[FocusFunction]:
        functions: list[FocusFunction] = []
        for item in evidence:
            if item.command_id != "symbol_table" or item.status != "completed":
                continue
            for line in item.stdout.splitlines():
                parts = line.split()
                if len(parts) < 8 or parts[3] != "FUNC" or parts[6] == "UND":
                    continue
                try:
                    address = int(parts[1], 16)
                    size = int(parts[2])
                except ValueError:
                    continue
                name = parts[7]
                functions.append(FocusFunction(name=name, address=address, size=size or None, reason="symbol-table"))
        return functions

    def _extract_angr_functions(self, evidence: list[CommandEvidence]) -> list[FocusFunction]:
        functions: list[FocusFunction] = []
        for item in evidence:
            if item.command_id != "angr_cfg" or item.status != "completed":
                continue
            payload = self._load_json_payload(item.stdout)
            if not isinstance(payload, dict):
                continue
            for entry in payload.get("functions", []) or []:
                if not isinstance(entry, dict):
                    continue
                addr = entry.get("addr")
                try:
                    address = int(str(addr), 16)
                except (TypeError, ValueError):
                    continue
                size = entry.get("size")
                functions.append(
                    FocusFunction(
                        name=str(entry.get("name") or hex(address)),
                        address=address,
                        size=int(size) if isinstance(size, int) and size > 0 else None,
                        reason="angr-cfg",
                    )
                )
        return functions

    def _extract_ida_functions(self, evidence: list[CommandEvidence]) -> list[FocusFunction]:
        functions: list[FocusFunction] = []
        for item in evidence:
            if item.command_id != "ida_batch" or item.status != "completed":
                continue
            payload = self._load_json_payload(item.stdout)
            if not isinstance(payload, dict):
                continue
            for entry in payload.get("function_index_preview", []) or []:
                if not isinstance(entry, dict):
                    continue
                address_value = entry.get("address") or entry.get("ea")
                if not address_value:
                    continue
                try:
                    address = int(str(address_value), 16)
                except (TypeError, ValueError):
                    continue
                functions.append(
                    FocusFunction(
                        name=str(entry.get("name") or hex(address)),
                        address=address,
                        reason="ida-preview",
                    )
                )
        return functions

    def _extract_dangerous_xref_callers(self, evidence: list[CommandEvidence]) -> set[str]:
        callers: set[str] = set()
        for item in evidence:
            if item.command_id != "rizin_overview" or item.status != "completed":
                continue
            payload = self._load_json_payload(item.stdout)
            if not isinstance(payload, dict):
                continue
            dangerous_xrefs = payload.get("dangerous_xrefs") or {}
            if not isinstance(dangerous_xrefs, dict):
                continue
            for refs in dangerous_xrefs.values():
                if not isinstance(refs, list):
                    continue
                for ref in refs:
                    if not isinstance(ref, dict):
                        continue
                    func_name = ref.get("function")
                    if isinstance(func_name, str) and func_name:
                        callers.add(func_name.lower())
        return callers

    def _extract_object_symbols(self, evidence: list[CommandEvidence]) -> dict[str, int]:
        symbols: dict[str, int] = {}
        for item in evidence:
            if item.command_id != "symbol_table" or item.status != "completed":
                continue
            for line in item.stdout.splitlines():
                parts = line.split()
                if len(parts) < 8 or parts[3] != "OBJECT" or parts[6] == "UND":
                    continue
                name = parts[7]
                try:
                    size = int(parts[2])
                except ValueError:
                    continue
                if size > 0:
                    symbols[name] = size
        return symbols

    def _extract_rizin_functions(self, evidence: list[CommandEvidence]) -> list[FocusFunction]:
        functions: list[FocusFunction] = []
        for item in evidence:
            if item.command_id != "rizin_overview" or item.status != "completed":
                continue
            payload = self._load_json_payload(item.stdout)
            if not isinstance(payload, dict):
                continue
            for entry in payload.get("functions", []) or []:
                if not isinstance(entry, dict):
                    continue
                offset = entry.get("offset")
                if not offset:
                    continue
                try:
                    address = int(str(offset), 16)
                except (TypeError, ValueError):
                    continue
                size = entry.get("size")
                functions.append(
                    FocusFunction(
                        name=str(entry.get("name") or hex(address)),
                        address=address,
                        size=int(size) if isinstance(size, int) and size > 0 else None,
                        reason="rizin-functions",
                    )
                )
        return functions

    def _summarize_function_disassembly(
        self,
        function: FocusFunction,
        stdout: str,
        object_symbols: dict[str, int],
    ) -> dict[str, Any]:
        instruction_pattern = re.compile(r"^\s*([0-9a-fA-F]+):\s+(?:[0-9a-fA-F]{2}\s+)+([a-z][a-z0-9]*)\s*(.*)$")
        tracked: dict[str, Any] = {}
        call_sites: list[dict[str, Any]] = []
        stack_frame_bytes: int | None = None
        local_offsets: set[int] = set()

        for raw_line in stdout.splitlines():
            match = instruction_pattern.match(raw_line)
            if not match:
                continue
            address = int(match.group(1), 16)
            mnemonic = match.group(2)
            operands = match.group(3).strip()

            if mnemonic == "sub" and operands.startswith("rsp,"):
                immediate = self._parse_immediate(operands.split(",", 1)[1].strip())
                if isinstance(immediate, int):
                    stack_frame_bytes = immediate

            local_offsets.update(self._extract_stack_offsets(operands))
            self._track_instruction(tracked, mnemonic, operands)

            if mnemonic != "call":
                continue

            call_target = self._extract_call_target(operands)
            args = {reg: tracked.get(reg) for reg in ("rdi", "rsi", "rdx", "rcx", "r8", "r9")}
            call_entry: dict[str, Any] = {
                "from": hex(address),
                "target": call_target,
                "args": self._sanitize_arg_snapshot(args),
            }
            issue = self._classify_call_site(call_target, args, stack_frame_bytes, object_symbols)
            if issue is not None:
                call_entry["issue"] = issue
            call_sites.append(call_entry)

        return {
            "name": function.name,
            "address": hex(function.address),
            "size": function.size,
            "reason": function.reason,
            "stack_frame_bytes": stack_frame_bytes,
            "local_stack_offsets": sorted(local_offsets),
            "call_sites": call_sites,
            "disassembly": stdout[:2400],
        }

    def _track_instruction(self, tracked: dict[str, Any], mnemonic: str, operands: str) -> None:
        if "," not in operands:
            if mnemonic == "xor":
                parts = [part.strip() for part in operands.split(",")]
                if len(parts) == 2 and parts[0] == parts[1]:
                    dest = self._normalize_register(parts[0])
                    if dest:
                        tracked[dest] = 0
            return

        left, right = [part.strip() for part in operands.split(",", 1)]
        dest = self._normalize_register(left)
        if dest is None:
            return

        if mnemonic == "lea":
            tracked[dest] = right
            return

        if mnemonic in {"mov", "movabs", "movzx", "movsxd"}:
            tracked[dest] = self._resolve_operand_value(right, tracked)
            return

        if mnemonic == "xor" and left == right:
            tracked[dest] = 0

    def _normalize_register(self, register: str) -> str | None:
        normalized = register.strip().lower()
        mapping = {
            "edi": "rdi",
            "rdi": "rdi",
            "esi": "rsi",
            "rsi": "rsi",
            "edx": "rdx",
            "rdx": "rdx",
            "ecx": "rcx",
            "rcx": "rcx",
            "eax": "rax",
            "rax": "rax",
            "r8d": "r8",
            "r8": "r8",
            "r9d": "r9",
            "r9": "r9",
        }
        return mapping.get(normalized)

    def _resolve_operand_value(self, operand: str, tracked: dict[str, Any]) -> Any:
        immediate = self._parse_immediate(operand)
        if isinstance(immediate, int):
            return immediate
        register = self._normalize_register(operand)
        if register is not None:
            return tracked.get(register, operand)
        return operand

    def _parse_immediate(self, operand: str) -> int | None:
        text = operand.strip()
        try:
            if text.startswith("0x"):
                return int(text, 16)
            if text.isdigit():
                return int(text)
        except ValueError:
            return None
        return None

    def _extract_stack_offsets(self, operands: str) -> set[int]:
        offsets: set[int] = set()
        for match in re.finditer(r"\[rbp-(0x[0-9a-fA-F]+|\d+)\]", operands):
            offsets.add(int(match.group(1), 16 if match.group(1).startswith("0x") else 10))
        for match in re.finditer(r"\[rsp\+(0x[0-9a-fA-F]+|\d+)\]", operands):
            offsets.add(int(match.group(1), 16 if match.group(1).startswith("0x") else 10))
        return offsets

    def _extract_call_target(self, operands: str) -> str:
        label_match = re.search(r"<([^>]+)>", operands)
        if label_match:
            return label_match.group(1)
        return operands.strip()

    def _sanitize_arg_snapshot(self, args: dict[str, Any]) -> dict[str, Any]:
        sanitized: dict[str, Any] = {}
        for key, value in args.items():
            if value is None:
                continue
            sanitized[key] = value
        return sanitized

    def _classify_call_site(
        self,
        target: str,
        args: dict[str, Any],
        stack_frame_bytes: int | None,
        object_symbols: dict[str, int],
    ) -> dict[str, Any] | None:
        normalized_target = target.split("@", 1)[0].replace("sym.imp.", "")
        if normalized_target in {"printf", "__printf_chk"}:
            format_arg = args.get("rdi")
            if self._is_suspicious_format_arg(format_arg):
                return {
                    "type": "format-string",
                    "evidence": f"{normalized_target} first-arg={format_arg}",
                }

        if normalized_target in {"read", "fgets", "gets"}:
            buffer_arg = args.get("rsi") if normalized_target == "read" else args.get("rdi")
            length_arg = args.get("rdx") if normalized_target == "read" else args.get("rsi")
            capacity = self._estimate_buffer_capacity(buffer_arg, object_symbols, stack_frame_bytes)
            if isinstance(length_arg, int) and isinstance(capacity, int) and length_arg > capacity:
                return {
                    "type": "overflow-candidate",
                    "evidence": f"{normalized_target} length={hex(length_arg)} capacity≈{hex(capacity)} buffer={buffer_arg}",
                }
        return None

    def _is_suspicious_format_arg(self, arg: Any) -> bool:
        if not isinstance(arg, str):
            return False
        if "[rbp-" in arg or "[rsp+" in arg:
            return True
        label_match = re.search(r"<([^>]+)>", arg)
        if not label_match:
            return False
        label = label_match.group(1)
        if label.startswith("_IO_stdin_used") or label.startswith(".rodata") or label.startswith("str."):
            return False
        return True

    def _estimate_buffer_capacity(
        self,
        buffer_arg: Any,
        object_symbols: dict[str, int],
        stack_frame_bytes: int | None,
    ) -> int | None:
        if isinstance(buffer_arg, str):
            stack_match = re.search(r"\[rbp-(0x[0-9a-fA-F]+|\d+)\]", buffer_arg)
            if stack_match:
                return int(stack_match.group(1), 16 if stack_match.group(1).startswith("0x") else 10)
            label_match = re.search(r"<([^>]+)>", buffer_arg)
            if label_match:
                label = label_match.group(1)
                if label in object_symbols:
                    return object_symbols[label]
        return stack_frame_bytes

    def _resolve_ida_binary(self) -> str | None:
        if self.settings.ida_headless_path is not None and self.settings.ida_headless_path.exists():
            return str(self.settings.ida_headless_path)

        candidates = (
            shutil.which("idat64"),
            shutil.which("idat"),
            str(Path.home() / "ida-pro-9.1" / "idat"),
            str(Path.home() / "ida-pro-9.1" / "idat64"),
        )
        for candidate in candidates:
            if candidate and Path(candidate).exists():
                return candidate
        return None

    def _resolve_rootfs_elf_exporter_script(self) -> Path | None:
        if self.settings.rootfs_elf_tool_dir is None:
            return None
        worker_script = self.settings.rootfs_elf_tool_dir / "ida_worker.py"
        if worker_script.exists():
            return worker_script
        return None

    def _resolve_ida_install_dir(self, executable: str) -> str | None:
        candidates: list[Path] = []
        if self.settings.host_ida_install_dir is not None:
            candidates.append(self.settings.host_ida_install_dir)
        if self.settings.ida_headless_path is not None:
            candidates.append(self.settings.ida_headless_path.parent)

        exe_path = Path(executable).resolve()
        candidates.extend([exe_path.parent, exe_path.parent.parent])

        for candidate in candidates:
            if candidate.exists() and (candidate / "idalib" / "python").exists():
                return str(candidate)
        return None

    def _summarize_rootfs_elf_ida_output(self, output_dir: Path, target: Path, ida_dir: str) -> tuple[str, dict[str, object]]:
        if not output_dir.exists():
            payload = {
                "input_file": str(target),
                "exporter": "rootfs_elf",
                "ida_dir": ida_dir,
                "artifacts": [],
            }
            metadata: dict[str, object] = {
                "exporter": "rootfs_elf",
                "artifact_dir": str(output_dir),
                "artifact_count": 0,
                "artifacts": [],
            }
            return json.dumps(payload, ensure_ascii=False, indent=2), metadata

        artifacts = sorted(
            str(path.relative_to(output_dir))
            for path in output_dir.rglob("*")
            if path.is_file()
        )
        imports_preview = self._read_preview_lines(output_dir / "imports.txt", limit=20)
        exports_preview = self._read_preview_lines(output_dir / "exports.txt", limit=20)
        strings_preview = self._read_preview_lines(output_dir / "strings.txt", limit=12)
        function_index_preview = self._read_jsonl_preview(output_dir / "function_index.jsonl", limit=12)
        source_preview = ""
        source_path = output_dir / "source.c"
        if source_path.exists():
            source_preview = source_path.read_text(encoding="utf-8", errors="replace")[:1600]

        payload = {
            "input_file": str(target),
            "exporter": "rootfs_elf",
            "ida_dir": ida_dir,
            "artifacts": artifacts[:80],
            "imports_preview": imports_preview,
            "exports_preview": exports_preview,
            "strings_preview": strings_preview,
            "function_index_preview": function_index_preview,
            "source_preview": source_preview,
        }
        metadata: dict[str, object] = {
            "exporter": "rootfs_elf",
            "artifact_dir": str(output_dir),
            "artifact_count": len(artifacts),
            "artifacts": artifacts[:80],
        }
        return json.dumps(payload, ensure_ascii=False, indent=2), metadata

    def _read_preview_lines(self, path: Path, limit: int) -> list[str]:
        if not path.exists():
            return []
        lines: list[str] = []
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                lines.append(line)
                if len(lines) >= limit:
                    break
        return lines

    def _read_jsonl_preview(self, path: Path, limit: int) -> list[dict[str, object]]:
        if not path.exists():
            return []
        items: list[dict[str, object]] = []
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for raw_line in handle:
                raw_line = raw_line.strip()
                if not raw_line:
                    continue
                try:
                    item = json.loads(raw_line)
                except json.JSONDecodeError:
                    continue
                items.append(
                    {
                        "name": item.get("name", ""),
                        "address": item.get("address", ""),
                        "is_entry_candidate": bool(item.get("is_entry_candidate", False)),
                        "entry_reason": item.get("entry_reason", ""),
                    }
                )
                if len(items) >= limit:
                    break
        return items

    def _unavailable_evidence(self, command_id: str, tool_name: str, reason: str) -> CommandEvidence:
        return CommandEvidence(
            command_id=command_id,
            command=[],
            return_code=127,
            tool_name=tool_name,
            status="unavailable",
            stderr=reason,
        )
