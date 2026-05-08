---
name: ctf-pwn
description: Solve CTF binary exploitation challenges by validating memory-corruption bugs, building reproducible exploits, and recovering flags from local or remote binaries. Use for stack/heap overflows, format strings, ROP/ret2libc, seccomp bypass, SROP, FSOP, or other pwn tasks. Prefer runtime evidence, disassembly, and locally generated ida-no-mcp exports via the bundled headless IDA wrapper; do not use Ghidra decompilation for this skill.
---

# CTF Binary Exploitation

## Purpose

Solve pwn challenges with hard evidence, reproducible exploits, and reusable post-challenge notes.

## Hard Rules

- Do not run Ghidra, ReVa, Binary Ninja decompiler, or other heavyweight decompilers for this skill.
- When a local binary is available, first try to generate or reuse `ida-no-mcp` exports with `scripts/export_headless_pseudocode.py`.
- Only ask the user for manual `ida-no-mcp` output when there is no local binary to run, or when there are multiple plausible target binaries and local inspection cannot disambiguate them.
- Treat auto-generated or user-provided pseudocode as lossy. Confirm important control flow, offsets, and data flow with disassembly or runtime evidence.
- Prefer facts from `file`, `checksec`, `readelf`, `objdump`, `strings`, `nm`, `ldd`, `gdb`/`pwndbg`, crash traces, leaks, and exploit trials.
- Keep debugger control fully agent-owned. Do not rely on the user to open GDB, switch windows, press `continue`, or paste commands.
- Do not use `pwntools.gdb.attach(...)` or `pwntools.gdb.debug(...)`. In pwntools they launch GDB through a separate terminal workflow, which is not autonomous enough for this skill.
- Separate facts, inferences, and assumptions in the response.
- Finish every completed challenge by updating the skill knowledge base. This is mandatory.

## Inputs

Collect or request only the missing artifacts that materially affect exploitability:

- Target binary, bundled `libc`, loader, Dockerfile, patch files, and remote endpoint
- Existing `export-for-ai` artifacts or user-provided `ida-no-mcp` exports, if already present
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

When a local binary is available:

1. Identify the primary target binary from the user prompt and local files.
2. If a complete `export-for-ai` directory already exists and is newer than the binary and the configured `INP.py`, reuse it.
3. Otherwise run `python scripts/export_headless_pseudocode.py /path/to/binary`.
4. If multiple ELF candidates remain after local inspection, ask the user which binary matters before exporting.
5. If the headless export fails, continue with disassembly and debugging. Do not block on pseudocode.

Read `references/headless_ida_export.md` when you need the export layout, fallback policy, or wrapper behavior.

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
4. Local or user-provided `ida-no-mcp` pseudocode
5. Generic heuristics from prior challenges

## Core Workflow

### 1. Generate or Reuse Decompilation Artifacts

- Prefer the bundled wrapper: `python scripts/export_headless_pseudocode.py /path/to/binary`
- The wrapper uses `CTF_PWN_IDAT_PATH` / `CTF_PWN_IDA_NO_MCP_PATH` when set, otherwise it falls back to common `idat` locations and then legacy `idat64` plus `INP.py`
- Default export location is next to the binary under `export-for-ai/`; default profile is `full`
- Reuse existing exports when the wrapper reports `status=reused`
- If the wrapper fails, note the failure reason from `idat.log` and keep moving with disassembly or debugging

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
- Headless decompilation: `python scripts/export_headless_pseudocode.py /path/to/binary`
- Existing or user-provided analysis input: `ida-no-mcp` exports only

## Prohibited Tooling

- Do not run Ghidra for decompilation under this skill
- Do not instruct the user to generate Ghidra output for you
- Do not block on missing pseudocode if disassembly and debugging already answer the question
- Do not skip the bundled headless export step when a local binary is available unless it already failed or is obviously unnecessary
- Do not use `pwntools.gdb.attach(...)`, `pwntools.gdb.debug(...)`, or any debugger helper that opens a new terminal, pane, or GUI window
- Do not ask the user to attach GDB manually, run a debugger in another shell, or babysit an interactive debugging session
- Do not leave `pause()` checkpoints or "attach now" comments as part of the normal exploit workflow
- Do not trust pseudocode over the debugger when they disagree

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

- `scripts/export_headless_pseudocode.py`: wrapper for `idat` with legacy `idat64` fallback plus `INP.py`, configurable through `CTF_PWN_IDAT_PATH` and `CTF_PWN_IDA_NO_MCP_PATH`
- `scripts/resolve_ubuntu_libc_bundle.py`: parse `strings libc.so.6 | grep Ubuntu`, infer `amd64` or `i386` from `file`, match the exact Ubuntu package id in local `glibc-all-in-one`, and download or reuse the full bundle
- `assets/pwntools_gdbserver_skeleton.py`: reusable pwntools exploit skeleton for local `gdbserver` launch, autonomous `gdb` control, and remote/local mode switching
- `$HOME/glibc-all-in-one`: local glibc package helper; use `list` or `old_list` plus `download` or `download_old` after extracting the Ubuntu package version from the provided libc
- `references/headless_ida_export.md`: headless export layout, reuse policy, and failure handling
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
