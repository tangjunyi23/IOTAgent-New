from pathlib import Path

from app.target_utils import ensure_target_executable


def test_ensure_target_executable_promotes_elf_mode(tmp_path: Path):
    sample = tmp_path / "pwn"
    sample.write_bytes(b"\x7fELFhello")
    sample.chmod(0o664)

    changed = ensure_target_executable(sample)

    assert changed is True
    assert sample.stat().st_mode & 0o111


def test_ensure_target_executable_ignores_plain_text(tmp_path: Path):
    sample = tmp_path / "notes.txt"
    sample.write_text("not an executable\n", encoding="utf-8")
    sample.chmod(0o664)

    changed = ensure_target_executable(sample)

    assert changed is False
    assert sample.stat().st_mode & 0o111 == 0
