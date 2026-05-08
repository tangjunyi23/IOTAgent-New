from __future__ import annotations

import stat
from pathlib import Path

EXECUTABLE_HEADERS: tuple[bytes, ...] = (
    b"\x7fELF",
    b"MZ",
    b"\xcf\xfa\xed\xfe",
    b"\xfe\xed\xfa\xcf",
    b"\xca\xfe\xba\xbe",
    b"\xbe\xba\xfe\xca",
)


def looks_like_executable_payload(path: Path) -> bool:
    try:
        header = path.read_bytes()[:4]
    except OSError:
        return False
    if header.startswith(b"#!"):
        return True
    return any(header.startswith(prefix) for prefix in EXECUTABLE_HEADERS)


def ensure_target_executable(path: Path) -> bool:
    try:
        if not path.exists() or not path.is_file():
            return False
        current_mode = path.stat().st_mode
        if current_mode & 0o111:
            return False
        if not looks_like_executable_payload(path):
            return False

        executable_bits = 0
        if current_mode & stat.S_IRUSR:
            executable_bits |= stat.S_IXUSR
        if current_mode & stat.S_IRGRP:
            executable_bits |= stat.S_IXGRP
        if current_mode & stat.S_IROTH:
            executable_bits |= stat.S_IXOTH
        if executable_bits == 0:
            executable_bits = stat.S_IXUSR

        path.chmod(current_mode | executable_bits)
        return True
    except OSError:
        return False
