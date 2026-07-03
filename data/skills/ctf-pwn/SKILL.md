---
name: ctf-pwn
description: Solve CTF binary exploitation challenges by validating memory-corruption bugs, building reproducible exploits, and recovering flags from local or remote binaries. Use for stack/heap overflows, format strings, ROP/ret2libc, seccomp bypass, SROP, FSOP, or other pwn tasks. Prefer runtime evidence, disassembly, and the vendored `scripts/rootfs_elf/` exporters (`scripts/rootfs_elf_single.py` for a single ELF, `scripts/rootfs_elf_batch.py` for rootfs batches); treat Ghidra decompilation as a last-resort fallback only.
---

# CTF Binary Exploitation

## Purpose

Solve pwn challenges with hard evidence, reproducible exploits, and reusable post-challenge notes.

## Hard Rules

- Do not start with Ghidra, ReVa, Binary Ninja decompiler, or other heavyweight decompilers for this skill. Use them only as a last resort after the preferred IDA and debugger-driven workflow has already failed to answer the exploitability question.
- When a local binary or extracted firmware/rootfs tree is available, first try to generate or reuse IDA exports with the vendored `scripts/rootfs_elf/` package.
- Before invoking the vendored IDA exporters, discover a usable local IDA installation yourself. Check `IDADIR` first, then common local installs such as `~/ida-pro-*`, `/opt/idapro*`, or other obvious local `ida*` directories; only ask the user for an IDA path after local discovery fails.
- Only ask the user for manual IDA export input when there is no local binary or rootfs tree to run locally, or when there are multiple plausible target binaries and local inspection cannot disambiguate them.
- Treat auto-generated or user-provided pseudocode as lossy, whether it came from `rootfs_elf` or another manual IDA export. Confirm important control flow, offsets, and data flow with disassembly or runtime evidence.
- Prefer facts from `file`, `checksec`, `readelf`, `objdump`, `strings`, `nm`, `ldd`, `gdb`/`pwndbg`, crash traces, leaks, and exploit trials.
- Keep debugger control fully agent-owned. Do not rely on the user to open GDB, switch windows, press `continue`, or paste commands.
- Do not use `pwntools.gdb.attach(...)` or `pwntools.gdb.debug(...)`. In pwntools they launch GDB through a separate terminal workflow, which is not autonomous enough for this skill.
- Separate facts, inferences, and assumptions in the response.
- Finish every completed challenge by updating the skill knowledge base. This is mandatory.

## Inputs

Collect or request only the missing artifacts that materially affect exploitability:

- Target binary, bundled `libc`, loader, Dockerfile, patch files, and remote endpoint
- Existing `export-for-ai` artifacts, `rootfs_elf` outputs, or other user-provided IDA exports, if already present
- Challenge description, expected IO protocol, and any local run notes
- Existing exploit or crash reproducer, if the user already has one

When a challenge ships a `libc.so.6`, treat version identification as mandatory early triage. Use the provided libc to recover the Ubuntu package version and, when possible, map it to a complete glibc bundle from local `glibc-all-in-one`.

## Reuse First

Before solving a new challenge:

1. Read `methodologies/index.md`.
2. Match prior entries by architecture, mitigation mix, vulnerability class, primitives, and `reuse_tags`.
3. Read the closest matching methodology documents.
4. Read `patterns.md` only for the relevant tags instead of treating it as a checklist.
5. Start with the previously decisive trick, then re-verify it against the current binary.

## Headless Decompile First

When a local binary or extracted tree is available:

1. Identify whether the target is a single ELF or a rootfs-like tree with many ELFs.
2. If a complete export already exists and is newer than the target binary or previous rootfs scan output is already present, reuse it.
3. Before running either exporter, locate a usable local IDA installation yourself and prefer passing it explicitly when the wrapper supports it.
4. For a single ELF, prefer `python3 scripts/rootfs_elf_single.py --elf /path/to/binary --out-dir /path/to/export-dir --ida-dir /path/to/ida`.
5. For extracted firmware or rootfs trees, prefer `IDADIR=/path/to/ida python3 scripts/rootfs_elf_batch.py /path/to/rootfs -o /path/to/out-dir --run-ida --workers 4 --progress`.
6. If multiple ELF candidates remain after local inspection, export the user-indicated challenge binary first; if the target is still ambiguous, ask the user before running a broad export.
7. If the `rootfs_elf` export fails and disassembly plus debugging still leave a material gap, Ghidra is allowed only as the final decompilation fallback. Treat its output as low-trust pseudocode and re-check every exploit-critical fact against disassembly or runtime evidence.

Read `references/headless_ida_export.md` when you need the export layout, reuse policy, or `rootfs_elf` command patterns.

## Autonomous GDB Workflow

When debugger evidence is needed:

1. Keep GDB in the same terminal session the agent already controls. Use a PTY-backed interactive session or a fully scripted `gdb -batch` / `gdb -ex ...` flow.
2. Prefer restarting the target under direct `gdb` control instead of attaching late. This makes the run reproducible and keeps the whole debugger lifecycle scripted.
3. Use late attach only when restart would lose the bug or materially change the state. Even then, attach from the same session with direct `gdb -p <pid>` commands, never through a helper that opens another window.
4. If interactive debugging is not paying for itself, fall back to `gdb -batch`, core files, `strace`, `ltrace`, or extra instrumentation instead of blocking on manual debugger work.

Read `references/gdb_usage.md` for the required command patterns, attach policy, fork handling, and evidence collection rules.

## Evidence Order

Use this order when sources disagree:

1. Runtime behavior and debugger state
2. ELF metadata and relocation or symbol tables
3. Disassembly and gadget search results
4. Local or user-provided `rootfs_elf` or other IDA-export pseudocode
5. Generic heuristics from prior challenges
6. Ghidra pseudocode used as a last-resort fallback

## Core Workflow

### 1. Generate or Reuse Decompilation Artifacts

- Prefer `scripts/rootfs_elf_single.py` for a single ELF and `scripts/rootfs_elf_batch.py` for rootfs batches.
- Discover a usable local IDA before running those wrappers. Reuse `IDADIR` when it is already set; otherwise probe common local installs yourself and pass `--ida-dir` for single-ELF exports or `IDADIR=/path/to/ida` for batch exports.
- For single binaries, choose an explicit export directory next to the sample, for example `export-for-ai/<binary-name>-rootfs-elf/`, so it is easy to reuse in later turns.
- Reuse existing exports when `source.c` plus the key indexes such as `function_index.jsonl`, `strings.txt`, and `imports.txt` are already present and newer than the target.
- Rootfs scans write `summary.json`, `indexes/`, and `by_elf/<elf_id>/...`; use `by_elf/` for per-binary artifacts and `indexes/` for cross-binary triage. Pass `-o` explicitly so the export lives next to the challenge instead of inside the skill directory.
- If `rootfs_elf` fails, note the reason from `ida.log` or the worker log, then continue with disassembly and debugging.

### 2. Triage the Binary

Run lightweight recon first:

- `file`
- `checksec --file`
- `ldd`
- `readelf -hW`, `readelf -lW`, `readelf -sW`, `readelf -rW`
- `objdump -d -Mintel`, `objdump -R`, `objdump -t`
- `strings -a -tx`

Record:

- Architecture, endianness, and libc or loader expectations
- Mitigations: NX, PIE, RELRO, canary, Fortify
- Obvious targets: `system`, `execve`, `/bin/sh`, GOT or PLT entries, win functions
- Any seccomp, sandbox, or syscall restrictions

If the challenge provides a libc, do this before deeper exploit planning:

- Prefer `python scripts/resolve_ubuntu_libc_bundle.py /path/to/libc.so.6` to automate the lookup and optional download flow.
- Run `strings /path/to/libc.so.6 | grep Ubuntu` to extract the Ubuntu glibc package string.
- Also run `file /path/to/libc.so.6` to confirm whether the package you need is `amd64` or `i386`.
- Normalize the package version from the `strings` output, for example `Ubuntu GLIBC 2.31-0ubuntu9.18` -> `2.31-0ubuntu9.18`.
- Search `$HOME/glibc-all-in-one/list` and `$HOME/glibc-all-in-one/old_list` for the exact package build with the right arch, for example `rg '^2\\.31-0ubuntu9\\.18_amd64$' "$HOME/glibc-all-in-one/list" "$HOME/glibc-all-in-one/old_list"`.
- If the version is missing or the local lists look stale, run `$HOME/glibc-all-in-one/update_list` and search again.
- Only do one refresh-and-search retry. If there is still no exact match, stop immediately; do not loop, do not guess nearby Ubuntu revisions, and do not keep retrying downloads.
- Use `$HOME/glibc-all-in-one/download <version_arch>` for entries found in `list`, or `$HOME/glibc-all-in-one/download_old <version_arch>` for entries found in `old_list`.
- Prefer the downloaded full glibc directory for matching `ld.so`, companion libraries, and debug symbols. Keep the originally provided libc as the ground truth when comparing bytes or symbol offsets.
- If no exact `glibc-all-in-one` match exists, continue with the provided libc and explicitly note that the full package could not be recovered automatically.

### 3. Map the IO and Attack Surface

- Identify all attacker-controlled inputs: stdin, argv, env, file, socket, menu choices
- Find loop structure, retry logic, fork model, and crash tolerance
- Locate parsing functions, copy sites, alloc or free sites, and indirect-call targets
- When runtime state matters, use the autonomous GDB workflow from `references/gdb_usage.md` instead of ad hoc attach-driven debugging
- If pseudocode exists, use it only to accelerate navigation; verify the key blocks with disassembly

### 4. Prove the Primitive

Do not call something exploitable until the decisive evidence is explicit:

- Overflow: destination size, write size, and overwrite target
- Format string: user-controlled format string and reachable read or write primitive
- Heap bug: chunk lifecycle, allocator state, and corruption target
- OOB or sign bug: exact arithmetic or path that creates the violation

Produce concrete facts:

- Offset, controllable bytes, bad-byte constraints, and alignment constraints
- Leak quality: stack, binary, libc, heap, canary
- Trigger conditions: one-shot, reusable, race-sensitive, fork-bruteforceable

### 5. Choose the Exploit Route

Pick the shortest route that matches the mitigations:

- `ret2win` when a direct target exists
- `ret2libc` or simple ROP when NX is on and a libc leak is available or derivable
- Leak-first chains for PIE, canary, ASLR, or full RELRO
- `open/read/write` instead of shell when seccomp or jailed IO makes shells unreliable
- Heap metadata attacks only when the primitive is real and the allocator version matters
- Consider `SROP`, `FSOP`, `setcontext`, or `_IO_FILE` style routes only when standard routes are blocked

### 6. Build a Reproducible Exploit

- Write exploit code with `pwntools` unless there is a concrete reason not to
- Make local exploitation deterministic before remote exploitation
- Parameterize binary path, remote host or port, libc, loader, offsets, and gadget addresses
- Keep helper functions small: start, debug, leak, resolve, send stage, get flag
- When you need pwntools-driven exploitation plus live debugger control, start from `assets/pwntools_gdbserver_skeleton.py` instead of rebuilding the same-session `gdbserver` flow from scratch
- If a debugger helper exists, make it launch direct same-session `gdb` commands or collect batch evidence. Do not leave `pause()` hooks or manual attach steps in the exploit.
- Record why each constant is trusted

### 7. Validate and Refine

- Re-test offsets and gadgets after each change
- Confirm calling convention and stack alignment
- Verify leaked addresses against ELF or libc math
- Check remote or local differences: libc, environment, line buffering, alarm, ASLR, fork server
- If a route fails, document why it failed before switching to another route

## Allowed Tooling

Prefer the smallest tool that proves the point:

- Static: `file`, `checksec`, `readelf`, `objdump`, `strings`, `nm`, `ldd`
- Dynamic: `gdb`, `pwndbg`, `strace`, `ltrace`
- Use `gdb` / `pwndbg` only through the same-session scripted workflow in `references/gdb_usage.md`
- Exploit: `pwntools`, `ROPgadget`, `ropper`, `one_gadget`, `patchelf`
- Headless decompilation: `python3 scripts/rootfs_elf_single.py --elf ... --out-dir ... --ida-dir /path/to/ida` or `IDADIR=/path/to/ida python3 scripts/rootfs_elf_batch.py ... --run-ida`
- Last-resort decompilation: Ghidra, only after the IDA-based paths plus disassembly and debugger evidence have proven insufficient
- Existing or user-provided analysis input: `rootfs_elf` exports or other IDA exports

## Prohibited Tooling

- Do not block on missing pseudocode if disassembly and debugging already answer the question
- Do not skip the vendored `scripts/rootfs_elf/` export step when a local binary or firmware tree is available unless it already failed or is obviously unnecessary
- Do not use `pwntools.gdb.attach(...)`, `pwntools.gdb.debug(...)`, or any debugger helper that opens a new terminal, pane, or GUI window
- Do not ask the user to attach GDB manually, run a debugger in another shell, or babysit an interactive debugging session
- Do not leave `pause()` checkpoints or "attach now" comments as part of the normal exploit workflow
- Do not trust pseudocode over the debugger when they disagree
- Do not treat Ghidra output as authoritative over disassembly, ELF metadata, or debugger state

## What to Return

Return a concise but evidence-driven answer with:

- If the flag was recovered, present `Flag: ...` before any summary or closing lesson section
- Vulnerability and decisive proof
- Mitigation picture and why the selected exploit route fits it
- Offsets, leaks, target addresses, and constraints
- Minimal exploit plan or finished exploit script
- Explicit facts versus assumptions
- After the flag, a closing section with `What this challenge taught`, `What future challenges this helps with`, and `Should patterns.md be updated?`

## Post-Challenge Update

After every completed challenge:

1. Create `methodologies/{challenge_slug}_{date}.md` using `references/methodology_generation.md`.
2. Add one row to `methodologies/index.md`.
3. Update `patterns.md` only if the lesson generalizes across challenges.
4. Preserve failed routes that taught something reusable.
5. Write the decisive insight in one sentence so future runs can find it quickly.

## Resources

- `scripts/rootfs_elf/`: vendored RootFS ELF analysis package, kept inside the skill so the workflow survives migration to another machine
- `scripts/rootfs_elf_single.py`: preferred single-ELF IDA exporter, producing `source.c`, `function_index.jsonl`, `decompile/`, `strings.txt`, `imports.txt`, `exports.txt`, `data_symbols.txt`, and optional `memory/`
- `scripts/rootfs_elf_batch.py`: preferred rootfs or multi-ELF batch IDA workflow, producing `summary.json`, `indexes/`, and per-ELF artifacts under `by_elf/`
- `scripts/resolve_ubuntu_libc_bundle.py`: parse `strings libc.so.6 | grep Ubuntu`, infer `amd64` or `i386` from `file`, match the exact Ubuntu package id in local `glibc-all-in-one`, and download or reuse the full bundle
- `assets/pwntools_gdbserver_skeleton.py`: reusable pwntools exploit skeleton for local `gdbserver` launch, autonomous `gdb` control, and remote/local mode switching
- `$HOME/glibc-all-in-one`: local glibc package helper; use `list` or `old_list` plus `download` or `download_old` after extracting the Ubuntu package version from the provided libc
- `references/headless_ida_export.md`: `rootfs_elf` export layout, reuse policy, and fallback handling
- `references/gdb_usage.md`: autonomous GDB usage rules for same-session debugging, batch evidence collection, and attach restrictions
- `patterns.md`: aggregated cross-challenge signals, primitives, and exploit routes
- `references/methodology_generation.md`: per-challenge write-up template and update rules
- `methodologies/index.md`: lookup table for prior solved challenges
- `methodologies/*.md`: detailed challenge-specific methodology notes

## Remember

Pwn work is a chain:

- find the primitive
- measure it
- match it to mitigations
- build the shortest reliable route to the flag
- save the lesson so the next challenge starts faster
