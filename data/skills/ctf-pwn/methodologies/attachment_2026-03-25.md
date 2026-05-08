# CTF Pwn Methodology: attachment

**Date**: 2026-03-25
**Binary**: `attachment`
**Architecture**: `x86_64`
**Mitigations**: `NX`, `Full RELRO`, `No PIE`, `Canary`, `SHSTK`, `IBT`, `No seccomp observed`
**Vulnerability Class**: stack overflow plus echo-based overread
**Primitives**: canary leak, saved-`rbp` leak, libc leak via `stdout` copy relocation, staged stack pivot, `execve` ROP
**Reuse Tags**: stack-overflow, canary-bypass, ret2libc, rop
**User-Provided ida-no-mcp Pseudocode**: no

## 1. Snapshot

- Goal: exploit `node6.anna.nssctf.cn:21228` and recover the remote flag.
- Artifacts used: local `attachment`, bundled `libc.so.6`, and a pwntools exploit script.
- The final remote command path was simple shell execution against `/flag`; the environment did not have `find`, so broad filesystem probes were less useful than direct reads.

## 2. Ground Truth

- `attachment` is a non-PIE amd64 ELF with `NX`, `Full RELRO`, stack canary, `SHSTK`, and `IBT`.
- The main vuln is not a format-string bug. The function first does `read(0, buf, 0x40)` into a stack area with only `0x38` safe bytes before the canary, then calls `printf("welcome %s\n", buf)`, then performs a second `read(0, buf, 0x80)`.
- Sending `b"A" * 0x39` overwrites the byte just past the local buffer and destroys the string terminator, so the fixed `%s` prints through the remaining 7 bytes of the canary and into saved `rbp`. The leak parser must strip the trailing newline because the literal is `welcome %s\n`, not `welcome %s`.
- A second payload with saved `rbp = 0x404050` and saved `rip = 0x40124f` re-enters the same print-and-read block from a fake frame in `.bss`. That makes `%s` print from `0x404010`, the executable's copy relocation for `stdout`, which yields a libc pointer after subtracting `_IO_2_1_stdout_`.
- Runtime evidence showed the next `read` also lands on `0x404010`, clobbering the copied `stdout` and `stdin` globals. A local `puts`-based route reached `libio/ioputs.c` and crashed, so anything that expected later stdio helpers to keep working was the wrong route.

## 3. Exploit Chain

- Leak stage 1:
  - Send `b"A" * 0x39`.
  - Parse the bytes after the marker, strip the trailing newline, reconstruct the canary as `b"\x00" + leak[:7]`, and decode the next 6 bytes as saved `rbp`.
- Leak stage 2:
  - Send `b"B" * 0x38 + p64(canary) + p64(0x404050) + p64(0x40124f)`.
  - Receive the `%s` output from `0x404010`, strip the trailing newline, and compute `libc_base = stdout_ptr - _IO_2_1_stdout_`.
- Pivot and staging:
  - Use `0x401279` to return from the fake `.bss` frame back onto the real stack.
  - Reuse `read@plt` plus the register state left by the vulnerable function to stage a larger payload on future `rsp`.
- Final stage:
  - Build `execve("/bin/sh", ["/bin/sh", "-c", command], NULL)` with libc gadgets.
  - This avoids any dependency on `puts`, `printf`, or other stdio paths after the `.bss` stage has corrupted the copy-relocated stream globals.
- Decisive insight: leak libc through the executable's copied `stdout` pointer, then immediately abandon stdio-dependent routes because the same fake-frame read that makes the leak possible also poisons those globals for the rest of the exploit.

## 4. Dead Ends Worth Remembering

- Treating the bug as a true format string was a trap. The format is fixed; the exploitability comes from the first `read` destroying the terminator before `%s`.
- Forgetting that the banner is `welcome %s\n` breaks every leak parser by leaving one extra newline byte on the end.
- A `puts` or parent-stdio route after the `.bss` leak stage is predictably unstable. The later `read` overwrites the copy-relocated stream pointers, so crashes in `ioputs` are a signal to stop using stdio entirely.

## 5. Lessons to Reuse

- Signals to watch for:
  - a first `read` that barely crosses the stack buffer boundary before the canary
  - an immediate fixed-format `%s` echo after that first read
  - a non-PIE binary with copy-relocated `stdin` or `stdout` pointers in writable memory
- Mitigation mix:
  - `Full RELRO` and `Canary` make a leak-first ret2libc route the natural default.
  - `No PIE` keeps the fake-frame target and copy-relocation addresses fixed, which makes the staged `%s` leaks straightforward.
- Reusable trick:
  - if you borrow the executable's copied `stdout` pointer as a `%s` leak source and the same code path performs a later `read` into that area, treat those stdio globals as single-use and pivot to raw `read@plt`, `execve`, or `orw` immediately after the leak.
- Should `patterns.md` be updated: yes. Add the single-use copy-relocation staging warning under the stack-overflow ret2libc/ROP pattern.

## 6. Deliverables

- Exploit script: `/home/tankuku/timu/attachment_extracted/exploit.py`
- Remote-specific adjustments:
  - default remote port updated to `21228`
  - the `"-c"` string in the final `argv` array must be padded to 8 bytes, otherwise `argv[2]` points at the second byte of the command string
  - simple commands were more reliable than tool-heavy probes because the remote shell lacked `find`
- Verified remote flag: `NSSCTF{bd06777a-6324-4dfb-b99b-7ff05f388af8}`
