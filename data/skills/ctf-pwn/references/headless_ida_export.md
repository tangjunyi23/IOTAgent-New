# Headless IDA Export

Prefer the vendored `scripts/rootfs_elf/` package for IDA work.

Use these entry points:

- Single ELF:
  - `python3 scripts/rootfs_elf_single.py --elf /path/to/binary --out-dir /path/to/export-dir --ida-dir /path/to/ida`
- Rootfs or many ELFs:
  - `IDADIR=/path/to/ida python3 scripts/rootfs_elf_batch.py /path/to/rootfs -o /path/to/out-dir --run-ida --workers 4 --progress`

Notes:

- Use the vendored wrappers, not direct package-file execution. `scripts/rootfs_elf_batch.py` handles the package import layout for you after migration.
- Before invoking the wrappers, discover a usable local IDA installation yourself. Check `IDADIR` first, then common local installs such as `~/ida-pro-*`, `/opt/idapro*`, or other obvious local `ida*` directories. Only ask the user for an IDA path after local discovery fails.
- For single-ELF exports, prefer passing `--ida-dir` explicitly even if you discovered the same path from `IDADIR`, so the command remains self-contained and portable in notes.
- For batch exports, `scripts/rootfs_elf_batch.py` can resolve IDA from the environment and common local install paths, but the agent should still verify a usable local install first instead of assuming one exists.
- For single binaries, choose a stable explicit output directory next to the sample, for example `export-for-ai/<binary-name>-rootfs-elf/`.
- Reuse existing exports when the key artifacts are already present and newer than the target.

`ida_worker.py` emits:

- `source.c`
- `function_index.jsonl`
- `decompile/*.c`
- `strings.txt`
- `imports.txt`
- `exports.txt`
- `data_symbols.txt`
- optional `memory/`

`scripts/rootfs_elf_batch.py` emits a batch layout:

- `summary.json`
- `indexes/elf_index.csv`
- `indexes/strings_global.jsonl`
- `indexes/imports_global.jsonl`
- `indexes/exports_global.jsonl`
- `indexes/entry_candidates.jsonl`
- `by_elf/<elf_id>/...` with the same per-ELF artifacts as `ida_worker.py`

Read the export in this order for a single target:

1. `function_index.jsonl` for navigation
2. `decompile/*.c` for function logic and call relationships
3. `source.c` for whole-program context and cross-references
4. `strings.txt`, `imports.txt`, `exports.txt`, `data_symbols.txt` for naming and reachability hints
5. `memory/` only when raw bytes materially help with exploitability
6. `decompile_failed.txt` or `decompile_skipped.txt` to spot imported stubs or decompiler blind spots

For rootfs batches, use `indexes/` first to pick the target ELF, then drop into `by_elf/<elf_id>/`.

When `rootfs_elf` fails:

- read the reported `ida.log` or worker log
- record whether the failure is IDA environment, loader, decompiler, or file-permission related
- if both IDA-based paths fail and `objdump`, `readelf`, and debugger evidence still leave a material gap, Ghidra is allowed only as the final fallback
- even then, treat Ghidra output as low-trust pseudocode and re-check every exploit-critical fact against disassembly or runtime evidence
