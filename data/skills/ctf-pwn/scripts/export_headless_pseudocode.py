#!/usr/bin/env python3

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_IDAT_CANDIDATES = (
    "/home/blonet/ida-pro-9.1/idat",
    "/opt/idapro/idat",
    "/opt/idapro/idat64",
)
DEFAULT_IDA_NO_MCP_CANDIDATES = (
    "/home/blonet/IDA-NO-MCP/INP.py",
    "/opt/IDA-NO-MCP/INP.py",
)
DEFAULT_PROFILE = "full"
VALID_PROFILES = ("full", "pwn")
REQUIRED_ARTIFACTS = (
    "decompile",
    "function_index.txt",
    "strings.txt",
    "imports.txt",
    "exports.txt",
)


def resolve_idat_path():
    env_path = os.environ.get("CTF_PWN_IDAT_PATH")
    if env_path:
        return Path(env_path).expanduser()

    for candidate in DEFAULT_IDAT_CANDIDATES:
        path = Path(candidate)
        if path.is_file():
            return path

    for program in ("idat", "idat64"):
        found = shutil.which(program)
        if found:
            return Path(found)

    return Path(DEFAULT_IDAT_CANDIDATES[0])


def resolve_ida_no_mcp_path():
    env_path = os.environ.get("CTF_PWN_IDA_NO_MCP_PATH")
    if env_path:
        return Path(env_path).expanduser()

    for candidate in DEFAULT_IDA_NO_MCP_CANDIDATES:
        path = Path(candidate)
        if path.is_file():
            return path

    return Path(DEFAULT_IDA_NO_MCP_CANDIDATES[0])


IDAT_PATH = resolve_idat_path()
IDA_NO_MCP_PATH = resolve_ida_no_mcp_path()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate or reuse headless IDA exports for the ctf-pwn skill."
    )
    parser.add_argument("binary_path", help="Path to the target binary")
    parser.add_argument(
        "--export-dir",
        help="Override the export directory. Defaults to export-for-ai/<name>-<sha256_8> next to the binary.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force a rebuild even if a fresh export already exists.",
    )
    parser.add_argument(
        "--profile",
        choices=VALID_PROFILES,
        default=DEFAULT_PROFILE,
        help="Export profile to request from IDA-NO-MCP.",
    )
    return parser.parse_args()


def sha256_prefix(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()[:8]


def ensure_writable_dir(path):
    path.mkdir(parents=True, exist_ok=True)
    probe = path / ".write_probe"
    try:
        probe.write_text("ok", encoding="utf-8")
    finally:
        if probe.exists():
            probe.unlink()


def choose_paths(binary_path, export_dir_override):
    artifact_key = "{}-{}".format(binary_path.name, sha256_prefix(binary_path))
    preferred_export_base = binary_path.parent / "export-for-ai"
    preferred_cache_base = binary_path.parent / ".ctf-pwn-idat"
    fallback_root = Path("/tmp/ctf-pwn-idat")

    if export_dir_override:
        export_dir = Path(export_dir_override).expanduser()
        if not export_dir.is_absolute():
            export_dir = Path.cwd() / export_dir
        export_dir = export_dir.resolve()
        ensure_writable_dir(export_dir)
        try:
            ensure_writable_dir(preferred_cache_base)
            cache_dir = preferred_cache_base / artifact_key
            strategy = "custom-export"
        except OSError:
            cache_dir = fallback_root / "cache" / artifact_key
            strategy = "custom-export+tmp-cache"
        ensure_writable_dir(cache_dir)
        return export_dir, cache_dir, strategy

    try:
        ensure_writable_dir(preferred_export_base)
        ensure_writable_dir(preferred_cache_base)
        export_dir = preferred_export_base / artifact_key
        cache_dir = preferred_cache_base / artifact_key
        strategy = "binary-dir"
    except OSError:
        export_dir = fallback_root / "export-for-ai" / artifact_key
        cache_dir = fallback_root / "cache" / artifact_key
        strategy = "tmp-fallback"

    ensure_writable_dir(export_dir)
    ensure_writable_dir(cache_dir)
    return export_dir, cache_dir, strategy


def required_paths(export_dir, profile):
    paths = [export_dir / name for name in REQUIRED_ARTIFACTS]
    if profile == "full":
        paths.append(export_dir / "memory")
    return paths


def artifacts_are_fresh(export_dir, binary_path, profile):
    required = required_paths(export_dir, profile)
    if not all(path.exists() for path in required):
        return False
    source_mtime = max(binary_path.stat().st_mtime, IDA_NO_MCP_PATH.stat().st_mtime)
    artifact_mtime = min(path.stat().st_mtime for path in required)
    return artifact_mtime >= source_mtime


def ida_script_arg(value):
    text = str(value)
    if any(char.isspace() for char in text):
        return '"{}"'.format(text.replace('"', '\\"'))
    return text


def build_ida_command(binary_path, export_dir, cache_dir, profile):
    database_path = cache_dir / "{}.i64".format(binary_path.name)
    log_path = cache_dir / "idat.log"
    script_switch = "-S{} {} 0 {} 1".format(
        ida_script_arg(IDA_NO_MCP_PATH),
        ida_script_arg(export_dir),
        profile,
    )
    command = [
        str(IDAT_PATH),
        "-c",
        "-A",
        "-o{}".format(database_path),
        "-L{}".format(log_path),
        script_switch,
        str(binary_path),
    ]
    return command, log_path


def print_summary(binary_path, export_dir, cache_dir, log_path, status, exit_code, strategy, profile):
    print("binary_path={}".format(binary_path))
    print("export_dir={}".format(export_dir))
    print("cache_dir={}".format(cache_dir))
    print("log_path={}".format(log_path))
    print("status={}".format(status))
    print("idat_exit_code={}".format(exit_code))
    print("path_strategy={}".format(strategy))
    print("profile={}".format(profile))


def main():
    args = parse_args()
    binary_path = Path(args.binary_path).expanduser()
    if not binary_path.is_absolute():
        binary_path = Path.cwd() / binary_path
    binary_path = binary_path.resolve()

    if not binary_path.is_file():
        print("binary_path is not a file: {}".format(binary_path), file=sys.stderr)
        return 2
    if not IDAT_PATH.is_file():
        print("idat not found: {}".format(IDAT_PATH), file=sys.stderr)
        return 2
    if not IDA_NO_MCP_PATH.is_file():
        print("IDA-NO-MCP script not found: {}".format(IDA_NO_MCP_PATH), file=sys.stderr)
        return 2

    export_dir, cache_dir, strategy = choose_paths(binary_path, args.export_dir)
    log_path = cache_dir / "idat.log"

    if not args.force and artifacts_are_fresh(export_dir, binary_path, args.profile):
        print_summary(binary_path, export_dir, cache_dir, log_path, "reused", 0, strategy, args.profile)
        return 0

    command, log_path = build_ida_command(binary_path, export_dir, cache_dir, args.profile)
    if log_path.exists():
        log_path.unlink()
    env = os.environ.copy()
    env["TVHEADLESS"] = "1"
    result = subprocess.run(
        command,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )

    print_summary(binary_path, export_dir, cache_dir, log_path, "rebuilt", result.returncode, strategy, args.profile)
    if result.returncode != 0 and result.stdout.strip():
        print(result.stdout.strip(), file=sys.stderr)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
