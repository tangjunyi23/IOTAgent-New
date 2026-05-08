from __future__ import annotations

import json
import re
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path

from app.config import Settings


@dataclass(frozen=True)
class PwnSkillNote:
    source: str
    content: str


class PwnSkillPack:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.skill_root = settings.skill_data_dir / settings.pwn_skill_dirname
        self.marker_path = self.skill_root / ".source.json"
        self.available = self._prepare()

    def _prepare(self) -> bool:
        zip_path = self.settings.pwn_skill_zip_path
        if zip_path is None or not zip_path.exists():
            return False

        source_state = {
            "zip_path": str(zip_path),
            "size": zip_path.stat().st_size,
            "mtime_ns": zip_path.stat().st_mtime_ns,
        }
        if self.skill_root.exists() and self.marker_path.exists():
            try:
                current_state = json.loads(self.marker_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                current_state = None
            if current_state == source_state and (self.skill_root / "SKILL.md").exists():
                return True

        temp_root = self.skill_root.parent / f".{self.skill_root.name}.tmp"
        if temp_root.exists():
            shutil.rmtree(temp_root)
        temp_root.mkdir(parents=True, exist_ok=True)
        extract_root = temp_root / self.skill_root.name

        with zipfile.ZipFile(zip_path) as archive:
            members = [name for name in archive.namelist() if name.startswith(f"{self.settings.pwn_skill_dirname}/")]
            archive.extractall(temp_root, members=members)

        if self.skill_root.exists():
            shutil.rmtree(self.skill_root)
        extract_root.replace(self.skill_root)
        self.marker_path.write_text(json.dumps(source_state, ensure_ascii=False, indent=2), encoding="utf-8")
        shutil.rmtree(temp_root, ignore_errors=True)
        return True

    def build_role_notes(self, role: str) -> list[PwnSkillNote]:
        if not self.available:
            return []

        notes = [
            PwnSkillNote(
                source="skill:ctf-pwn",
                content=(
                    "已启用 ctf-pwn skill：优先使用运行时证据、反汇编、ELF 元数据和已导出的 IDA/angr 结果；"
                    "不要把伪代码、经验或外部资料伪装成已验证事实。"
                ),
            )
        ]

        if role in {"dynamic-analysis", "exploit-strategy", "exploitability-review", "static-analysis"}:
            notes.extend(
                [
                    PwnSkillNote(
                        source="skill:ctf-pwn:gdb",
                        content=(
                            "GDB 必须由 agent 全程脚本化驱动：优先使用同 session 的 gdb -batch / gdb -ex 流程，"
                            "不要依赖人工 attach、pause 或外部终端。"
                        ),
                    ),
                    PwnSkillNote(
                        source="skill:ctf-pwn:poc",
                        content=(
                            "若已拿到足够证据，应输出已验证 POC：给出最小触发载荷、运行命令或最小 pwntools 脚本，"
                            "并说明它是如何被运行时证据证实的。"
                        ),
                    ),
                ]
            )

        if role in {"dynamic-analysis", "exploit-strategy"}:
            notes.append(
                PwnSkillNote(
                    source="skill:ctf-pwn:template",
                    content=(
                        f"可复用的 pwntools+gdbserver 模板位于 {self.skill_root / 'assets' / 'pwntools_gdbserver_skeleton.py'}，"
                        "需要脚本化动态验证时可参考其 same-session GDB 控制方式。"
                    ),
                )
            )

        return notes

    def poc_template_path(self) -> Path | None:
        path = self.skill_root / "assets" / "pwntools_gdbserver_skeleton.py"
        return path if self.available and path.exists() else None

    def gdb_reference_excerpt(self, *, limit: int = 480) -> str:
        if not self.available:
            return ""
        path = self.skill_root / "references" / "gdb_usage.md"
        if not path.exists():
            return ""
        text = path.read_text(encoding="utf-8")
        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip() and not line.startswith(("#", "```"))
        ]
        compact = re.sub(r"\s+", " ", " ".join(lines))
        return compact[:limit].rstrip() + ("…" if len(compact) > limit else "")
