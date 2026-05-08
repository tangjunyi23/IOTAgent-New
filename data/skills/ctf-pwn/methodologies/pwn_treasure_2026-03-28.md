# CTF Pwn Methodology: pwn-treasure

**Date**: 2026-03-28
**Binary**: `attachments/pwn-treasure`
**Architecture**: x86_64
**Mitigations**: NX, Partial RELRO, PIE, Canary, SHSTK, IBT
**Vulnerability Class**: signed index arbitrary write with same-address `%s` leak
**Primitives**: signed OOB qword write, libc leak via copy-relocated `stdout`, constrained libc `one_gadget`
**Reuse Tags**: ret2libc
**User-Provided ida-no-mcp Pseudocode**: no

## 1. Snapshot

- The binary asks for a fake password, then offers two signed `%lld` index selections that each feed an 8-byte `read(0, base + idx*8, 8)`.
- The write base is binary-relative `.bss` (`base + 0x40a0`), so negative indices reach `.got.plt`, `.data`, and the copied stdio globals.
- Remote endpoint: `nc1.ctfplus.cn:19381`.

## 2. Ground Truth

- `file` / `checksec`: 64-bit PIE, NX, Canary, Partial RELRO, SHSTK, IBT.
- Disassembly shows the first password check compares a user-supplied `unsigned long long` against `base + 0x1209`, so blind guessing is not viable under PIE.
- The real bug is the signed index path:
  - `scanf("%lld", &qword_48a0)`
  - only `idx > 0xff` is rejected with signed `jg`
  - the program then performs `read(0, base+0x40a0 + idx*8, 8)`
  - immediately followed by `printf("after your operation, the context: %s", base+0x40a0 + idx*8)`
- Writing 8 non-NUL bytes immediately before a useful pointer turns that `%s` echo into a leak without needing an existing read primitive.
- Runtime memory inspection confirmed that `.bss+0x4060` is the copy-relocated `_IO_2_1_stdout_` pointer, so `idx = -9` leaks libc.

## 3. Exploit Chain

- First write:
  - choose `idx = -9` to write at `.data+0x4058`
  - send `b"A"*8`
  - the trailing bytes printed by `%s` leak `_IO_2_1_stdout_`
  - compute `libc_base = leak - libc.sym["_IO_2_1_stdout_"]`
- Stack shaping:
  - the later name read stores controlled bytes at `rbp-0x90`
  - send `b"A"*0x20 + b"\\x00"*8 + b"\\n"` so `[rbp-0x70] == NULL`
- Final control-flow hijack:
  - choose `idx = -13` to overwrite `printf@got`
  - write `libc_base + 0xebd43`
  - this `one_gadget` works because the call site already sets `eax = 0`, `[rbp-0x70]` was forced to NULL, and the referenced stack slots are writable
- Final route: libc leak -> GOT overwrite -> constrained `one_gadget`
- Decisive insight: the easiest leak is not PIE but the copy-relocated `_IO_2_1_stdout_` pointer, and the same stack frame already contains a user-filled buffer that can be arranged to satisfy the winning `one_gadget` constraints.

## 4. Dead Ends Worth Remembering

- Tried leaking PIE from the self-pointer at `.data+0x4058` and then jumping back into binary code through `printf@got`.
- Failed because the interesting mid-function targets (`system("/bin/sh")` branch and hidden `scanf` branch) are reached without a fresh prologue, so their later libc calls hit misaligned-stack `movaps` crashes.
- Earlier warning: if the hijacked target is a mid-function block that immediately calls libc, check stack alignment before committing to that route.

## 5. Lessons to Reuse

- When a signed index arbitrary write is followed by `%s` from the same address, start by writing just before copy-relocated globals such as `stdout`, `stdin`, or resolved GOT slots.
- A later stack-local input can sometimes be used to satisfy `one_gadget` constraints; treat gadget constraints as part of stack-layout analysis, not as an afterthought.
- Partial RELRO plus a final post-write `printf` call makes `printf@got` a natural code-execution target, even when the primitive is only two writes.
- Should `patterns.md` be updated: no. The exact `one_gadget` constraint shaping here is useful, but still challenge-specific enough that it does not yet justify a generalized pattern entry.

## 6. Deliverables

- Exploit script: `attachments/solve.py`
- Remote-specific adjustments: use the shipped `libc.so.6` and subtract `_IO_2_1_stdout_`; the working remote gadget was `0xebd43`.
- Remaining assumptions or things not fully verified:
  - headless IDA export failed because no valid IDA license was available
  - local validation was done against the host libc with an equivalent `one_gadget`; the final gadget offset was confirmed directly on the remote target
