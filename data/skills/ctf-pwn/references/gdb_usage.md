# Autonomous GDB Usage

Use GDB to collect runtime evidence, not as a handoff point to the user. The agent must own the full debugger lifecycle.

## Hard Rules

- Keep GDB in the same terminal session the agent already controls.
- Do not use `pwntools.gdb.attach(...)` or `pwntools.gdb.debug(...)`. In pwntools both routes spawn GDB through a separate terminal workflow.
- Do not tell the user to open another shell, switch to a new pane, or press `continue`.
- Prefer command-driven runs over free-form interactive poking. If a session cannot be reproduced as commands, it is not yet good enough evidence.

## Default Order

1. Start with `gdb -batch` or `gdb -ex ...` when you only need crash evidence, register state, a backtrace, memory dumps, or one or two breakpoint hits.
2. Use a single PTY-backed interactive GDB session when you need iterative stepping, breakpoint edits, or repeated inspection in one run.
3. Attach to an already running PID only when restart would lose the state you need.
4. If GDB is slowing progress, switch to core files, `strace`, `ltrace`, logging, or exploit-side instrumentation.

## Baseline Commands

Use these defaults unless the target gives you a reason not to:

```gdb
set pagination off
set confirm off
set breakpoint pending on
set print thread-events off
set disassemble-next-line on
handle SIGALRM nostop noprint pass
handle SIGPIPE nostop noprint pass
```

Add more `handle` rules only for signals the binary actually expects.

## Preferred Launch Patterns

For restartable local targets, run GDB directly instead of going through pwntools helpers:

```sh
gdb -q --args ./chall arg1 arg2
```

or for one-shot evidence:

```sh
gdb -q -batch --args ./chall arg1 arg2 \
  -ex 'set pagination off' \
  -ex 'set breakpoint pending on' \
  -ex 'break *main' \
  -ex 'run' \
  -ex 'bt' \
  -ex 'info registers'
```

For interactive work, keep the debugger inside one PTY session the agent can continue driving. Do not split to another pane or rely on a GUI debugger.

For pwntools-driven exploits that still need live debugger control, use `assets/pwntools_gdbserver_skeleton.py`. It starts the local target under `gdbserver`, returns a normal exploit tube for pwntools IO, and opens a second same-session GDB tube the agent can drive directly.

## Attach Policy

Late attach is the exception, not the default.

- Use attach only when the bug depends on an already-running process, forked child state, or a setup path that is materially harder to reproduce from the start.
- Attach from the same session with direct `gdb -q -p <pid>` commands or scripted `-batch -p <pid>` evidence collection.
- Set the executable explicitly with `file /path/to/binary` if symbols are missing after attach.
- After attach, immediately collect the minimal evidence you need: stop reason, `bt`, registers, stack or heap bytes, mappings, and the relevant pointer chain.

Example:

```sh
gdb -q -batch -p "$pid" \
  -ex 'set pagination off' \
  -ex 'file ./chall' \
  -ex 'x/i $pc' \
  -ex 'bt' \
  -ex 'info registers' \
  -ex 'x/16gx $rsp'
```

## Forking and Child Processes

When the challenge forks or daemonizes, decide the fork policy up front and script it:

```gdb
set follow-fork-mode child
set detach-on-fork off
```

If the parent is the only interesting process, keep `follow-fork-mode parent`. Do not discover this by manually clicking around after the fact.

## Shared Libraries and Early Breakpoints

For dynamically linked binaries:

- Break on `_start`, a known executable address, or a challenge function first.
- Do not assume libc symbols are available before the loader finishes.
- If you need libc symbols early, use `set breakpoint pending on` and continue until the libraries are loaded.

## Evidence to Record

Every debugger session should produce concrete output you can cite later:

- crash site: `x/i $pc`
- call chain: `bt`
- register state: `info registers`
- stack or heap bytes: `x/16gx $rsp`, `x/32bx <addr>`, or architecture-appropriate variants
- mappings when ASLR or heap layout matters: `info proc mappings` or `vmmap` if pwndbg helps
- the exact breakpoint or watchpoint condition that proved the primitive

Prefer standard GDB commands for anything you plan to cite. `pwndbg` commands like `context`, `telescope`, and `vmmap` are useful accelerators, but they are optional enhancements, not the primary source of truth.

## Exploit Integration

If an exploit script has a debug mode:

- make it run the target normally and separately launch direct GDB commands in the same controlled session, or
- make it collect batch evidence and exit cleanly.
- when you need a live pwntools tube and a live debugger at the same time, prefer a startup-under-`gdbserver` pattern over late attach. The reusable skeleton in `assets/pwntools_gdbserver_skeleton.py` is the default starting point.

Do not ship exploit helpers that depend on:

- `pause()` waiting for a human to attach
- comments like `# attach gdb here`
- `gdb.attach(...)`
- `gdb.debug(...)`
- opening a tmux split, a new terminal window, or a GUI app

## When to Stop Debugging

Leave GDB once you have the decisive fact:

- exact overwrite offset
- verified leak source and normalization
- allocator or FILE state at the corruption point
- syscall, seccomp, or sandbox behavior that changes the exploit route

If the debugger is no longer answering the next exploit question, switch back to exploitation work.
