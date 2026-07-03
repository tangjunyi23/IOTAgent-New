from pathlib import Path

from app.config import Settings
from app.models import CommandEvidence
from app.toolbox import BinaryToolbox, FocusFunction


def build_settings(tmp_path: Path) -> Settings:
    data_dir = tmp_path / "data"
    runtime_dir = data_dir / "runtime"
    frontend_dir = tmp_path / "frontend"
    docs_dir = tmp_path / "docs"
    ida_root = tmp_path / "ida-pro"
    exporter_dir = tmp_path / "rootfs_elf"

    (ida_root / "idalib" / "python").mkdir(parents=True)
    (ida_root / "idat").write_text("", encoding="utf-8")
    exporter_dir.mkdir()
    (exporter_dir / "ida_worker.py").write_text("# test exporter\n", encoding="utf-8")

    return Settings(
        data_dir=data_dir,
        upload_dir=data_dir / "uploads",
        audit_dir=data_dir / "audits",
        artifact_meta_dir=data_dir / "artifacts",
        runtime_dir=runtime_dir,
        frontend_dir=frontend_dir,
        progress_log_path=docs_dir / "PROGRESS.md",
        ida_headless_path=ida_root / "idat",
        host_ida_install_dir=ida_root,
        rootfs_elf_tool_dir=exporter_dir,
        host_workspace_dir=tmp_path,
    )


def test_ida_capability_prefers_rootfs_elf_exporter(tmp_path: Path):
    settings = build_settings(tmp_path)
    toolbox = BinaryToolbox(settings)

    capability = toolbox._build_capability("ida_batch")

    assert capability.available is True
    assert capability.metadata["exporter"] == "rootfs_elf"
    exporter_script = capability.metadata["exporter_script"]
    assert exporter_script.endswith(("rootfs_elf_single.py", "ida_worker.py"))
    assert Path(exporter_script).exists()


def test_rizin_capability_prefers_vendored_radare2(tmp_path: Path):
    settings = build_settings(tmp_path)
    vendor_bin = settings.host_workspace_dir / ".vendor" / "radare2" / "root" / "usr" / "bin"
    vendor_bin.mkdir(parents=True)
    (vendor_bin / "radare2").write_text("", encoding="utf-8")
    (vendor_bin / "rabin2").write_text("", encoding="utf-8")
    (vendor_bin / "radare2").chmod(0o755)
    (vendor_bin / "rabin2").chmod(0o755)

    toolbox = BinaryToolbox(settings)
    capability = toolbox._build_capability("rizin_overview")

    assert capability.available is True
    assert capability.executable == str(vendor_bin / "radare2")


def test_function_disasm_summary_detects_format_string_and_overflow(tmp_path: Path):
    settings = build_settings(tmp_path)
    toolbox = BinaryToolbox(settings)
    function = FocusFunction(name="main", address=0x4011B6, size=0xA8, reason="test")
    summary = toolbox._summarize_function_disassembly(
        function,
        """
  401227:\tba 00 01 00 00       \tmov    edx,0x100
  40122c:\t48 8d 05 4d 2e 00 00 \tlea    rax,[rip+0x2e4d]        # 404080 <buf>
  401233:\t48 89 c6             \tmov    rsi,rax
  401236:\tbf 00 00 00 00       \tmov    edi,0x0
  40123b:\te8 70 fe ff ff       \tcall   4010b0 <read@plt>
  401240:\t48 8d 05 39 2e 00 00 \tlea    rax,[rip+0x2e39]        # 404080 <buf>
  401247:\t48 89 c7             \tmov    rdi,rax
  40124a:\tb8 00 00 00 00       \tmov    eax,0x0
  40124f:\te8 4c fe ff ff       \tcall   4010a0 <printf@plt>
        """,
        {"buf": 0x40},
    )

    issues = [
        site["issue"]["type"]
        for site in summary["call_sites"]
        if isinstance(site, dict) and "issue" in site
    ]

    assert "overflow-candidate" in issues
    assert "format-string" in issues


def test_plan_follow_up_prefers_function_disasm_on_first_round(tmp_path: Path):
    settings = build_settings(tmp_path)
    toolbox = BinaryToolbox(settings)

    evidence = [
        CommandEvidence(
            command_id="symbol_table",
            command=["readelf", "-Ws", "/tmp/sample"],
            return_code=0,
            stdout=(
                "    21: 0000000000401202    81 FUNC    GLOBAL DEFAULT   15 get_info\n"
                "    38: 0000000000401253    60 FUNC    GLOBAL DEFAULT   15 main\n"
                "    33: 00000000004011bd    13 FUNC    GLOBAL DEFAULT   15 my_gadget\n"
                "    35: 0000000000404080   512 OBJECT  GLOBAL DEFAULT   26 buf\n"
            ),
        ),
        CommandEvidence(
            command_id="rizin_overview",
            command=["radare2", "--structured-overview", "/tmp/sample"],
            return_code=0,
            stdout=(
                '{"dangerous_xrefs":{"printf":[{"function":"main","from":"0x40124f"}],'
                '"read":[{"function":"get_info","from":"0x401230"}]}}'
            ),
        ),
    ]

    requests = toolbox.plan_follow_up("triage", evidence, 0)

    assert len(requests) == 1
    assert requests[0].command_id == "function_disasm"


def test_plan_follow_up_can_use_peer_shared_focus_function(tmp_path: Path):
    settings = build_settings(tmp_path)
    toolbox = BinaryToolbox(settings)

    evidence = [
        CommandEvidence(
            command_id="rizin_overview",
            command=["radare2", "--structured-overview", "/tmp/sample"],
            return_code=0,
            stdout='{"linked_libraries":["libc.so.6"]}',
        )
    ]

    requests = toolbox.plan_follow_up(
        "triage",
        evidence,
        0,
        peer_notes=["[来自static-analysis/discussion/update/函数协查] main @ 0x4011b6 需要继续下钻。"],
    )

    assert len(requests) == 1
    assert requests[0].command_id == "function_disasm"
    assert requests[0].payload["functions"][0]["name"] == "main"


def test_plan_follow_up_can_schedule_new_disasm_after_previous_round(tmp_path: Path):
    settings = build_settings(tmp_path)
    toolbox = BinaryToolbox(settings)

    evidence = [
        CommandEvidence(
            command_id="function_disasm",
            command=["objdump", "--focus-disasm", "/tmp/sample"],
            return_code=0,
            stdout=(
                '{"functions":['
                '{"name":"main","address":"0x4011b6","call_sites":['
                '{"from":"0x40124f","target":"printf@plt","issue":{"type":"format-string","evidence":"printf first-arg=buf"}}'
                "]}]}"
            ),
        ),
        CommandEvidence(
            command_id="function_xrefs",
            command=["radare2", "--focus-xrefs", "/tmp/sample"],
            return_code=0,
            stdout='{"functions":[{"name":"main","address":"0x4011b6","caller_count":1,"callers":[{"function":"entry0","from":"0x401090"}]}]}',
        ),
    ]

    requests = toolbox.plan_follow_up(
        "static-analysis",
        evidence,
        5,
        peer_notes=["[来自dynamic-analysis/discussion/question/函数协查] get_info @ 0x401202 需要继续下钻。"],
    )

    assert len(requests) == 1
    assert requests[0].command_id == "function_disasm"
    assert requests[0].payload["functions"][0]["name"] == "get_info"


def test_plan_follow_up_schedules_gdb_poc_for_format_string_issue(tmp_path: Path):
    settings = build_settings(tmp_path)
    toolbox = BinaryToolbox(settings)

    evidence = [
        CommandEvidence(
            command_id="rizin_overview",
            command=["radare2", "--structured-overview", "/tmp/sample"],
            return_code=0,
            stdout='{"functions":[{"name":"main","offset":"0x4011b6","size":168}]}',
        ),
        CommandEvidence(
            command_id="function_disasm",
            command=["objdump", "--focus-disasm", "/tmp/sample"],
            return_code=0,
            stdout=(
                '{"functions":['
                '{"name":"main","address":"0x4011b6","call_sites":['
                '{"from":"0x40123b","target":"read@plt","issue":{"type":"overflow-candidate","evidence":"read length=0x100 capacity≈0x40 buffer=buf"}},'
                '{"from":"0x40124f","target":"printf@plt","issue":{"type":"format-string","evidence":"printf first-arg=buf"}}'
                "]}]}"
            ),
        )
    ]

    requests = toolbox.plan_follow_up("dynamic-analysis", evidence, 2)

    assert len(requests) == 1
    assert requests[0].command_id == "gdb_poc"
    assert requests[0].payload["functions"][0]["issue_type"] == "format-string"
    assert requests[0].payload["functions"][0]["breakpoint"] == 0x40124F


def test_native_payload_probe_uses_full_output_for_validation(tmp_path: Path):
    settings = build_settings(tmp_path)
    toolbox = BinaryToolbox(settings)
    sample = tmp_path / "probe.py"
    sample.write_text(
        "\n".join(
            [
                "#!/usr/bin/env python3",
                "import sys",
                "sys.stdin.read()",
                "print('A' * 1300 + 'FMT_PROBE.0x1337')",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    sample.chmod(0o755)

    result = toolbox._run_native_payload_probe(sample, "FMT_PROBE.%p.%p.%p.%p\n")

    assert result["validated"] is True
    assert result["probe_line"].endswith("FMT_PROBE.0x1337")
    assert "FMT_PROBE.0x1337" not in result["stdout_preview"]


def test_format_string_exploit_script_uses_generic_pointer_leak_assertion(tmp_path: Path):
    settings = build_settings(tmp_path)
    toolbox = BinaryToolbox(settings)
    script = toolbox._build_format_string_exploit_script(
        target=tmp_path / "sample.bin",
        payload="FMT_PROBE.%p.%p.%p.%p\n",
        breakpoint_address=0x40124F,
        native_probe={"probe_line": "Your message: FMT_PROBE.0x7fff1234.(nil)"},
    )

    assert "import re" in script["content"]
    assert "gdb.debug" not in script["content"]
    assert "process(context.binary.path)" in script["content"]
    assert "probe_line = next((line for line in output.splitlines() if b'FMT_PROBE.' in line), b'')" in script["content"]
    assert "re.search(rb'0x[0-9a-fA-F]{4,}', probe_line)" in script["content"]
    assert "0x404080" not in script["content"]
    assert script["expected_output"] == "Your message: FMT_PROBE.0x7fff1234.(nil)"
