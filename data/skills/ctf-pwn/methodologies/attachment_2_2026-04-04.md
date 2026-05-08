# CTF Pwn Methodology: attachment_2

**Date**: 2026-04-04
**Binary**: `pwn`
**Architecture**: `x86_64`
**Mitigations**: `NX`, `Partial RELRO`, `No PIE`, `No Canary`, `SHSTK`, `IBT`, `No seccomp observed`
**Vulnerability Class**: `format string in a global .bss buffer`
**Primitives**: `_exit@got` partial overwrite to recursive `main`, libc leak from recursive frame, single-call `printf@got -> system` dual overwrite
**Reuse Tags**: `fmt`
**User-Provided ida-no-mcp Pseudocode**: `no`

## 1. Snapshot

- Goal: exploit `114.66.24.221:41828` and recover the remote flag.
- Artifacts used: local `pwn`, bundled `libc.so.6`, bundled `ld-linux-x86-64.so.2`, pwntools exploit.
- Runtime quirk: input is read into a global `buf` with `read(0, buf, 0x100)` and the program never appends a NUL, so every stage payload must include an explicit `\x00` terminator or later rounds inherit stale format-string tail bytes and crash.

## 2. Ground Truth

- `pwn` is a small non-PIE amd64 ELF with `Partial RELRO`, `NX`, `No Canary`, `SHSTK`, and `IBT`.
- The bug is direct: `read(0, buf, 0x100)` into global `buf` at `0x404080`, then `printf(buf)`, then `_exit(0)`.
- Because `buf` is in `.bss`, attacker-controlled addresses are not automatically present on the variadic stack. The exploit depends on runtime argument layout, not on appending raw pointers to the payload.
- Debugger evidence before the first `printf` showed:
  - `rsi == buf`, `rdx == 0x100`
  - stack arg 8 points to slot 16, and slot 16 starts as `0x403e00`
  - stack arg 27 leaks `__libc_start_main+0x8b`
- After rewriting `_exit@got` to `main`, the next recursive frame has a different layout:
  - stack arg 10 points to slot 18, and slot 18 starts as `0x404000`
  - stack arg 26 points to slot 44, whose value starts as `1`
  - stack arg 29 still leaks `__libc_start_main+0x8b`
- The debugger proved the recursive frame layout shift. Reusing first-frame fmt offsets after the first `_exit -> main` jump is wrong.

## 3. Exploit Chain

- Stage 1:
  - Use the first-frame `arg8 -> slot16` alias to turn slot 16 into `_exit@got`.
  - Later in the same `printf`, use slot 16 itself to write `_exit@got = main`.
  - Continue consuming arguments until arg 27 and print `%p` to leak `__libc_start_main+0x8b`.
- Stage 2:
  - In the first recursive frame, use `arg10 -> slot18` to retarget slot 18 from `0x404000` to `printf@got`.
  - Use arg 18 to write the low two bytes of `system`.
  - Use `arg26 -> slot44` plus one large `%n` to synthesize `printf@got+2` inside slot 44.
  - Use arg 44 to write the third byte of `system`, completing `printf@got -> system` in the same call.
- Stage 3:
  - Send `cat /flag || cat flag || cat /home/ctf/flag\x00`.
  - The next `printf(buf)` actually executes `system(buf)`.
- Decisive insight: the first fmt write is only a bootstrap; once `_exit@got` jumps back into `main`, you must treat the recursive frame as a new fmt puzzle and use its `arg10 -> slot18` plus `arg26 -> slot44` aliases to finish `printf@got -> system` in one call.

## 4. Dead Ends Worth Remembering

- Treating the challenge like a normal amd64 fmt where addresses are appended to the payload was a trap. The format string lives in `.bss`, so no attacker pointers land on the variadic stack automatically.
- Sending newline-terminated payloads without `\x00` caused later rounds to inherit the previous stage's stale format string and crash. The global buffer, not the fmt math, was the real reason those attempts died.
- Reusing first-frame argument positions after `_exit@got -> main` failed because every recursive round inserts another `main` frame and shifts the useful slots.

## 5. Lessons to Reuse

- Signals to watch for:
  - global `.bss` format strings where appended pointers are useless
  - `_exit(0)` immediately after `printf(buf)`
  - stack aliases that point at other stack argument slots containing already-good `0x40xxxx` values
- Mitigation mix:
  - `Partial RELRO` makes the shortest route a GOT overwrite, and `No PIE` keeps the needed `.got/.data` addresses fixed.
  - The lack of a canary is irrelevant here because there is no stack write primitive; the fmt alias graph is the real exploit surface.
- Reusable trick:
  - when the program exits right after a fmt call, check whether a cheap partial GOT overwrite can turn that exit edge into a recursive re-entry, then map the new variadic layout separately instead of assuming the old one still applies.
- Should `patterns.md` be updated: no. The recursive-frame alias graph is useful, but it is still challenge-specific enough to keep in a methodology note.

## 6. Deliverables

- Exploit script: `/home/tankuku/timu/pwn/attachment_2/exploit.py`
- Remote-specific adjustments:
  - remote leak offset used: `__libc_start_main+0x8b`
  - stage 2 prints about `0x404012` bytes to build a second pointer in a zeroed stack slot
  - every stage payload must be NUL-terminated
- Verified remote flag: `flag{900d_W0rK_f0R_cH3ck1n!_574R7_Y0Ur_NC7F_pl33Z}`
