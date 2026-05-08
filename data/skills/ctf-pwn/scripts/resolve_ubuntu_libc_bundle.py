#!/usr/bin/env python3

import argparse
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path


DEFAULT_GLIBC_ALL_IN_ONE = Path(os.environ.get("GLIBC_ALL_IN_ONE_HOME", "~/glibc-all-in-one")).expanduser()
COMMON_URL = "https://mirror.tuna.tsinghua.edu.cn/ubuntu/pool/main/g/glibc/"
OLD_URL = "http://old-releases.ubuntu.com/ubuntu/pool/main/g/glibc/"
PACKAGE_REGEX = re.compile(r"libc6_(2\.[0-9]+-[0-9]+ubuntu[0-9.]*_(?:amd64|i386))\.deb")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Resolve a provided Ubuntu libc.so.6 to a matching glibc-all-in-one bundle."
    )
    parser.add_argument("libc_path", help="Path to the provided libc.so.6")
    parser.add_argument(
        "--glibc-dir",
        default=str(DEFAULT_GLIBC_ALL_IN_ONE),
        help="Path to the local glibc-all-in-one checkout. Default: %(default)s",
    )
    parser.add_argument(
        "--no-download",
        action="store_true",
        help="Only resolve the package id and matching list entry; do not run download/download_old.",
    )
    parser.add_argument(
        "--no-update-list",
        action="store_true",
        help="Do not retry with glibc-all-in-one/update_list if the first lookup misses.",
    )
    return parser.parse_args()


def run_command(argv, cwd=None):
    return subprocess.run(
        argv,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )


def fail(message, exit_code=2):
    print(message, file=sys.stderr)
    raise SystemExit(exit_code)


def resolve_architecture(libc_path):
    result = run_command(["file", str(libc_path)])
    if result.returncode != 0:
        fail("failed to inspect libc with file:\n{}".format(result.stdout.strip()))

    output = result.stdout.strip()
    if "ELF 64-bit" in output and "x86-64" in output:
        return "amd64", output
    if "ELF 32-bit" in output and "Intel 80386" in output:
        return "i386", output
    fail("unsupported libc architecture from file output: {}".format(output))


def extract_ubuntu_version(libc_path):
    result = run_command(["strings", str(libc_path)])
    if result.returncode != 0:
        fail("failed to inspect libc with strings:\n{}".format(result.stdout.strip()))

    ubuntu_lines = []
    for line in result.stdout.splitlines():
        if "Ubuntu GLIBC" not in line:
            continue
        ubuntu_lines.append(line.strip())
        match = re.search(r"Ubuntu GLIBC ([0-9][^)\s]+)", line)
        if match:
            return match.group(1), line.strip()

    if ubuntu_lines:
        fail("found Ubuntu GLIBC marker but could not parse version from: {}".format(ubuntu_lines[0]))
    fail("no Ubuntu GLIBC version string found in {}".format(libc_path))


def read_package_list(path):
    if not path.is_file():
        return set()
    with path.open("r", encoding="utf-8") as handle:
        return {line.strip() for line in handle if line.strip()}


def find_package_id(glibc_dir, package_id):
    for list_name in ("list", "old_list"):
        entries = read_package_list(glibc_dir / list_name)
        if package_id in entries:
            return list_name
    return None


def fetch_remote_package_list(url):
    try:
        with urllib.request.urlopen(url, timeout=20) as response:
            content = response.read().decode("utf-8", errors="ignore")
    except urllib.error.URLError as exc:
        raise RuntimeError(str(exc)) from exc

    return set(PACKAGE_REGEX.findall(content))


def refresh_package_lists_in_memory():
    refreshed = {}
    refreshed["list"] = fetch_remote_package_list(COMMON_URL)
    refreshed["old_list"] = fetch_remote_package_list(OLD_URL)
    return refreshed


def ensure_bundle_downloaded(glibc_dir, package_id, list_name):
    bundle_dir = glibc_dir / "libs" / package_id
    if bundle_dir.is_dir():
        return "reused", bundle_dir, ""

    script_name = "download_old" if list_name == "old_list" else "download"
    script_path = glibc_dir / script_name
    if not script_path.is_file():
        fail("glibc-all-in-one helper not found: {}".format(script_path))

    result = run_command([str(script_path), package_id], cwd=glibc_dir)
    if result.returncode != 0:
        fail("glibc-all-in-one {} failed:\n{}".format(script_name, result.stdout.strip()))
    if not bundle_dir.is_dir():
        fail("glibc-all-in-one {} reported success but bundle is missing: {}".format(script_name, bundle_dir))
    return "downloaded", bundle_dir, result.stdout.strip()


def print_summary(
    libc_path,
    glibc_dir,
    arch,
    file_output,
    ubuntu_version,
    ubuntu_line,
    package_id,
    list_name,
    update_attempted,
    update_status,
    update_error,
    bundle_status,
    bundle_dir,
    stop_reason,
):
    print("libc_path={}".format(libc_path))
    print("glibc_dir={}".format(glibc_dir))
    print("arch={}".format(arch))
    print("file_output={}".format(file_output))
    print("ubuntu_version={}".format(ubuntu_version))
    print("ubuntu_line={}".format(ubuntu_line))
    print("package_id={}".format(package_id))
    print("matched_list={}".format(list_name or ""))
    print("update_attempted={}".format("yes" if update_attempted else "no"))
    print("update_status={}".format(update_status))
    print("update_error={}".format(update_error or ""))
    print("bundle_status={}".format(bundle_status))
    print("bundle_dir={}".format(bundle_dir or ""))
    print("stop_reason={}".format(stop_reason or ""))


def main():
    args = parse_args()
    libc_path = Path(args.libc_path).expanduser()
    if not libc_path.is_absolute():
        libc_path = Path.cwd() / libc_path
    libc_path = libc_path.resolve()

    glibc_dir = Path(args.glibc_dir).expanduser()
    if not glibc_dir.is_absolute():
        glibc_dir = Path.cwd() / glibc_dir
    glibc_dir = glibc_dir.resolve()

    if not libc_path.is_file():
        fail("libc_path is not a file: {}".format(libc_path))
    if not glibc_dir.is_dir():
        fail("glibc-all-in-one directory not found: {}".format(glibc_dir))

    arch, file_output = resolve_architecture(libc_path)
    ubuntu_version, ubuntu_line = extract_ubuntu_version(libc_path)
    package_id = "{}_{}".format(ubuntu_version, arch)

    update_attempted = False
    update_status = "not_needed"
    update_error = None
    list_name = find_package_id(glibc_dir, package_id)
    # Only try one refresh pass. If the exact package still does not exist, stop.
    if list_name is None and not args.no_update_list:
        update_attempted = True
        try:
            refreshed_lists = refresh_package_lists_in_memory()
            update_status = "remote_refreshed"
            for candidate in ("list", "old_list"):
                if package_id in refreshed_lists.get(candidate, set()):
                    list_name = candidate
                    break
            if list_name is None:
                update_status = "remote_no_match"
        except RuntimeError as exc:
            update_status = "remote_refresh_failed"
            update_error = str(exc)
    elif args.no_update_list:
        update_status = "skipped"

    if list_name is None:
        print_summary(
            libc_path,
            glibc_dir,
            arch,
            file_output,
            ubuntu_version,
            ubuntu_line,
            package_id,
            None,
            update_attempted,
            update_status,
            update_error,
            "aborted_no_exact_match",
            None,
            "no_exact_glibc_all_in_one_match",
        )
        return 1

    if args.no_download:
        print_summary(
            libc_path,
            glibc_dir,
            arch,
            file_output,
            ubuntu_version,
            ubuntu_line,
            package_id,
            list_name,
            update_attempted,
            update_status,
            update_error,
            "matched_only",
            None,
            None,
        )
        return 0

    bundle_status, bundle_dir, _download_output = ensure_bundle_downloaded(glibc_dir, package_id, list_name)
    print_summary(
        libc_path,
        glibc_dir,
        arch,
        file_output,
        ubuntu_version,
        ubuntu_line,
        package_id,
        list_name,
        update_attempted,
        update_status,
        update_error,
        bundle_status,
        bundle_dir,
        None,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
