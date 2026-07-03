# CTF Pwn Methodology: borrowstack

**Date**: 2026-05-13
**Binary**: `attachment-27`
**Architecture**: `i386`
**Mitigations**: `NX`, `Partial RELRO`, `No PIE`, `No Canary`
**Vulnerability Class**: stack overflow
**Primitives**: raw stack smash, contiguous GOT leak via `puts(read@got)`, leak-first ret2libc
**Reuse Tags**: stack-overflow, ret2libc, rop
**User-Provided ida-no-mcp Pseudocode**: no

## 1. Snapshot

- The service at `39.96.193.120:10002` prints `Sometimes you need to step onto someone else's ground.` once and then performs a single oversized `read`.
- Local artifacts used: only the ELF `attachment-27`; no bundled libc or loader were provided.
- The remote libc was identified from leaked symbol offsets as the Ubuntu 32-bit compatibility libc shipped by `libc6-i386_2.31-0ubuntu9.17/18_amd64`.

## 2. Ground Truth

- `file`, `checksec`, and `readelf` showed a 32-bit non-PIE executable with NX, partial RELRO, and no stack canary.
- `prologue` is not dead code: it runs from `.init_array`, disables buffering on all stdio streams, and prints the banner before `main`.
- `vul` allocates `buf[64]` at `[ebp-0x50]` and then executes `read(0, buf, 0x100)`, so the saved return address is directly controllable after `84` bytes.
- The import surface is tiny: only `read`, `puts`, `setvbuf`, and `__libc_start_main` are imported, with no win function and no `/bin/sh` consumer in the binary.
- A quick `ret2dlresolve` attempt was a dead end here. The 32-bit loader path plus `.gnu.version` checks made the forged relocation route less reliable than a plain leak-first ret2libc.

## 3. Exploit Chain

- Use `cyclic` and the generated corefile to confirm the saved-`EIP` offset is `84`.
- Stage 1 returns into `puts@plt`, uses `pop ebx; ret` at `0x08049022` as the cleanup gadget, passes `read@got`, and then returns back to `vul`.
- Because `puts` treats the GOT entry as a C string, it does not stop after four bytes. It leaks the adjacent GOT entries too, so one call returned four libc pointers in order: `read`, `puts`, `__libc_start_main`, and `setvbuf`.
- Match the low 12-bit tuple `read=0x790`, `puts=0x1e0`, `__libc_start_main=0xde0`, `setvbuf=0x9c0` with `libc.rip`, which identifies the remote libc as `libc6-i386_2.31-0ubuntu9.17/18_amd64`.
- Stage 2 reuses the second `vul` invocation and overwrites the return address with `system`, a dummy return, and the libc `"/bin/sh"` pointer.
- After the shell starts on the same socket, send `cat /flag || cat flag || find / -maxdepth 2 -name flag 2>/dev/null | head -n 5`.
- Decisive insight: once `puts(read@got)` was observed to spill across consecutive GOT slots, a single first-stage ret2libc leak uniquely fingerprinted the remote libc and made a normal `system("/bin/sh")` finish shorter and safer than `ret2dlresolve`.

## 4. Dead Ends Worth Remembering

- Route attempted: two-stage stack pivot plus `ret2dlresolve`.
- Why it failed: the 32-bit forged relocation path was much more fragile here than it first looked, and the service did not need it because a clean libc leak was already available through imported `puts`.
- Earlier warning sign: when a no-canary non-PIE i386 binary already imports `puts` and exposes a writable GOT slot with no interior NUL bytes, leak-first ret2libc should beat `ret2dlresolve` unless the imports are truly insufficient.

## 5. Lessons to Reuse

- On small i386 stack overflows, inspect the imported functions before defaulting to fancy loader tricks. `puts@plt(got_entry)` is often enough to bootstrap libc if the GOT layout is contiguous and the leak can run until the first zero byte.
- A single string-style leak from one GOT entry can fingerprint libc better than a strict 4-byte read because adjacent relocation targets often sit back-to-back in `.got.plt`.
- `ret2dlresolve` on 32-bit partial-RELRO binaries is useful, but it should lose priority when the binary already offers a simpler imported-output leak primitive.
- Should `patterns.md` be updated: yes. Add a stack-overflow cue that `puts(got_entry)` may leak several adjacent GOT slots and turn one ROP call into a multi-symbol libc fingerprint.

## 6. Deliverables

- Exploit script: `/home/tankuku/timu/pwn/borrowstack_exploit.py`
- Remote-specific adjustments: use the libc offsets from `libc6-i386_2.31-0ubuntu9.17/18_amd64`; both revisions share the offsets needed here.
- Verified remote flag: `flag{caefa3f9-c458-43d4-abad-bc6ec17bc225}`
