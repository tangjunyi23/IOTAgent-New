# CTF Pwn Methodology: pwn-throne-hazard

**Date**: 2026-03-28
**Binary**: `attachments/pwn`
**Architecture**: x86_64
**Mitigations**: NX, Full RELRO, No PIE, Canary, FORTIFY, SHSTK, IBT, seccomp
**Vulnerability Class**: TOCTOU-gated heap overflow into a heap-resident dispatch object
**Primitives**: race-triggered heap overflow, copy-relocated `stdout` leak, dispatch-table retargeting, ORW via `open`/`readv`/`write`
**Reuse Tags**: heap-overflow, orw
**User-Provided ida-no-mcp Pseudocode**: no

## 1. Snapshot

- The menu exposes three important objects:
  - a `0x30` "capsule" heap chunk allocated by option 2
  - a `0x48` "actuator" heap chunk allocated by option 3
  - a background thread that periodically raises the global `supremacy floor`
- Remote endpoint: `nc1.ctfplus.cn:18249`.
- Local artifacts used: shipped `pwn`, `libc.so.6`, and `ld-linux-x86-64.so.2`.
- The practical flag assumption was that the remote flag lived at `/flag`, but the final exploit kept a short candidate list.

## 2. Ground Truth

- `file` / `checksec`: 64-bit non-PIE executable, NX, Full RELRO, Canary, FORTIFY, SHSTK, IBT.
- `strings` already points at the real bug: "One stale read. One fresh write. A heartbeat decides the champion."
- Static disassembly proved the race in option 2:
  - it first checks `floor <= 0x20`
  - then sets a shared flag
  - later, after another thread may have changed `floor`, it re-reads `floor` and uses `floor + 0xf` as the stream length
- The worker thread at `0x401df0` waits a randomized `120000..299999` usec, raises `floor` to the attacker-chosen target, then keeps it high for roughly `18000..35999` usec before restoring `0x20`.
- When the attacker delays the 1-byte primer until that window, option 2 switches from a safe `0x2f` read to a `0x87` read and overflows the `0x30` capsule into the adjacent actuator allocation.
- The actuator layout is decisive:
  - `+0x10`: lane index
  - `+0x18`: length
  - `+0x20`: pointer
  - dispatch calls one of four function-table slots from writable `.data` at `0x4040e0`
- The original slots are:
  - lane 0: `write(1, ptr, len)`
  - lane 1: exact `read(0, ptr, len)`
  - lane 2: FNV-1a digest printer
  - lane 3: `memset(ptr, 0, len)` then print `scrubbed`
- Runtime tests proved that the easiest leak is the copy-relocated `stdout` object at `0x404100`; setting `lane=0, len=8, ptr=&stdout` leaks `_IO_2_1_stdout_`.
- Decoding the embedded seccomp BPF showed the important restriction: the filter blocks `execve`, `execveat`, `mmap`, `mprotect`, `pkey_mprotect`, `writev`, `clone`, `fork`, `vfork`, and `clone3`, but leaves ordinary file I/O alone.
- That seccomp fact mattered more than pseudocode: `system()` and direct `execve()` looked attractive, but both silently failed because the filter rejects process-creation syscalls with `EPERM`.

## 3. Exploit Chain

- Heap setup:
  - allocate the capsule once with a normal `0x2f` forge
  - allocate the actuator second so it sits immediately after the capsule
- Stage 1: libc leak
  - repeatedly race option 2 until the prompt flips from `0x2f bytes left` to `0x87 bytes left`
  - overflow the actuator to `lane=0`, `len=8`, `ptr=&stdout`
  - dispatch and compute `libc_base = leak - libc.sym["_IO_2_1_stdout_"]`
- Stage 2: dispatch-table retargeting
  - preserve lane 0 and lane 1
  - replace lane 2 with `open`
  - replace lane 3 with `readv`
- Stage 3: helper blob
  - use lane 1 to write an `0x80`-byte blob into `0x404160`
  - layout:
    - short path string at `0x404160`
    - a 3-entry `iovec` array at `0x404178`
    - read buffer at `0x4041a8`
- Stage 4: ORW
  - overflow to `lane=2`, `len=0`, `ptr=path_ptr` and dispatch `open(path, O_RDONLY, 2)`
  - assume fd `3`, since only stdio fds are open
  - overflow to `lane=3`, `len=iovec_ptr`, `ptr=3` and dispatch `readv(3, iov, 3)`
  - overflow to `lane=0`, `len=0x38`, `ptr=buf_ptr` and dump the buffer with the original `write`
- Final route: race -> heap overflow -> libc leak -> dispatch-table rewrite -> ORW
- Decisive insight: once seccomp proved that `execve`-style wins were fake, the shortest route was to keep lane 0 as the built-in `write`, repurpose lanes 2 and 3 to `open` and `readv`, and treat the actuator as a tiny syscall multiplexer.

## 4. Dead Ends Worth Remembering

- Tried replacing lane 0 with `system`.
- Failed because the seccomp filter rejects the process-creation path used by `system()`, so dispatch returned cleanly without running the shell command.
- Earlier warning: if embedded seccomp BPF explicitly blocks `execve` and `clone` family syscalls, do not spend more time on shell-based wins.

- Tried replacing lane 0 with direct `execve`.
- Failed for the same reason: the wrapper reaches the blocked `execve` syscall and returns `-1`.
- Earlier warning: when the filter returns `SECCOMP_RET_ERRNO`, "clean" failure is expected; lack of a crash does not mean the call worked.

- Initially overfilled the helper blob past `0x4041e0`.
- Failed because that clobbered the global actuator pointer and later menu actions died.
- Earlier warning: the writable `.bss` staging area ended exactly at `0x4041df`; keep helper data strictly inside that boundary.

## 5. Lessons to Reuse

- If a challenge gives you a heap-resident dispatcher object with `(fn_index, len, ptr)` fields, think in terms of "retarget selected slots" rather than "full control-flow hijack".
- A race that only changes a read length can still be enough when the next heap object is itself an interpreter for useful libc wrappers.
- Copy-relocated stdio objects are still one of the cheapest Full RELRO libc leaks in non-PIE binaries.
- When seccomp blocks code-exec syscalls but leaves file I/O syscalls untouched, prefer ORW with existing wrappers over shell-oriented plans.
- Should `patterns.md` be updated: no. The high-level lesson is useful, but the exact race timing plus dispatcher layout are still challenge-specific.

## 6. Deliverables

- Exploit script: `/home/tankuku/timu/pwn/pwn-throne-hazard/solve.py`
- Remote-specific adjustments:
  - race timing had to scan a delay set instead of using a single local-friendly delay
  - the successful remote flag path was `/flag`
- Remaining assumptions or things not fully verified:
  - headless IDA export failed because no valid IDA license was available
  - fd `3` was assumed after `open`; this matched both local and remote behavior
