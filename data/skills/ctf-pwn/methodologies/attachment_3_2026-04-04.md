# CTF Pwn Methodology: attachment_3

**Date**: 2026-04-04
**Binary**: `pwn`
**Architecture**: `x86_64`
**Mitigations**: `NX`, `Partial RELRO`, `No PIE`, `No Canary`, `SHSTK`, `IBT`, seccomp allowing `read`/`write`/`open`/`close`/`exit`/`exit_group`/`rt_sigreturn`
**Vulnerability Class**: custom softlink metadata confusion leading to arbitrary read/write
**Primitives**: arbitrary read, arbitrary write, libc leak via GOT, stack leak via `environ`, stack ROP, seccomp-safe ORW via raw syscalls
**Reuse Tags**: rop, seccomp, orw
**User-Provided ida-no-mcp Pseudocode**: no

## 1. Snapshot

- Goal: exploit `114.66.24.221:49149` and recover the remote flag.
- Artifacts used: local `pwn`, bundled `libc.so.6`, and a pwntools/pexpect exploit script.
- The service is a tiny in-memory VFS with commands `LIST`, `READ`, `WRITE`, `TOUCH`, `HARDLINK`, `SOFTLINK`, and `QUIT`.

## 2. Ground Truth

- `pwn` is a non-PIE amd64 ELF with `NX`, `Partial RELRO`, no canary, `SHSTK`, and `IBT`.
- The obvious `/dev/stack_core` target is admin-only; direct `READ /dev/stack_core ...` returns `ERR permission denied`.
- `cmd_softlink` does not resolve names. It interprets the source file's contents as a link blob when:
  - the source is not already a softlink,
  - `size > 0x17`,
  - `ptr != NULL`,
  - and `memcmp(src->ptr + 0x10, "LNKPTR", 6) == 0`.
- The created softlink copies `ptr`, `size`, and sometimes `perm` directly out of the attacker-controlled blob:
  - `ptr = *(void **)(blob + 0x0)`
  - `size = *(uint32_t *)(blob + 0x8)`
  - `perm = *(uint32_t *)(blob + 0xc)` unless the source is a hardlink
- `cmd_read` and `cmd_write` only check the inode permission bit and then trust `inode->ptr` / `inode->size`, so a forged softlink becomes an arbitrary read/write primitive.
- The seccomp filter allows syscall number `2` (`open`) but not `257` (`openat`). Glibc `open()` in the bundled 2.39 libc issues `openat`, so a normal libc call would be killed by seccomp.

## 3. Exploit Chain

- Stage 1: create a regular file and `WRITE` a fake `LNKPTR` blob into it.
- Stage 2: `SOFTLINK` that file into a new inode with attacker-chosen `ptr`, `size`, and `perm=0`.
- Stage 3: use the fake softlink to leak `read@got`, then compute `libc_base` from `read`.
- Stage 4: use another fake softlink to leak `environ`, then dump a stack window around it.
- Stage 5: scan that stack dump for the `menu_loop -> vfs_sandbox -> handle_client` return-address pattern:
  - `0x402c68`
  - `0x402ca3` at `+0xe10`
  - `0x402d11` at `+0xe30`
- Stage 6: create a final fake softlink targeting the saved return address of `menu_loop` and overwrite it with a ROP chain.
- Final route: raw-syscall ORW from libc gadgets:
  - `rax=2; syscall` for `open("/flag", 0, 0)`
  - assume returned fd is `3`
  - `rax=0; syscall` for `read(3, buf, 0x100)`
  - `rax=1; syscall` for `write(1, buf, 0x100)`
  - `rax=60; syscall` for `exit(0)`
- Decisive insight: once `SOFTLINK` was confirmed to deserialize attacker-controlled file contents into `ptr/size/perm`, the challenge stopped being a VFS puzzle and became arbitrary read/write plus a seccomp-aware stack ROP exercise.

## 4. Dead Ends Worth Remembering

- `/dev/stack_core` looked like the intended stack leak, but the admin-only permission bit blocks the direct path; the right move was to bypass permissions with a forged softlink instead of trying to clone that inode directly.
- Calling glibc `open()` under this seccomp profile is a trap on modern glibc, because the wrapper uses `openat`; the syscall whitelist must be checked against wrapper behavior, not just symbol names.
- There is no need to hunt for a classic stack overflow just because the binary is named `VFS_Stack`; the real bug is object reinterpretation inside the custom VFS layer.

## 5. Lessons to Reuse

- Signals to watch for:
  - custom filesystem, IPC, or object stores that serialize pointers, sizes, or permissions into user-controlled blobs
  - "link" or "descriptor" creation paths that compare a magic tag and then copy fields directly out of attacker-controlled memory
  - seccomp filters that whitelist legacy syscalls but not the newer wrappers glibc now uses internally
- Mitigation picture:
  - `No PIE` made the return-address signatures and gadget math stable.
  - The arbitrary read/write primitive made the lack of canary largely irrelevant; the shortest finish was a stack overwrite and ORW.
  - Seccomp made raw syscalls better than libc wrappers.
- Reusable trick:
  - if you can forge a link-like metadata blob with `ptr`, `size`, and `perm`, first spend it on a libc leak, then on `environ`, then overwrite a saved return address directly instead of overcomplicating the route.
- Should `patterns.md` be updated: no. The lesson is useful, but the exact "fake VFS softlink blob" signal is still too challenge-specific to promote into the generic pattern library.

## 6. Deliverables

- Exploit script: `/home/tankuku/timu/pwn/attachment_3/exploit.py`
- Remote-specific adjustments:
  - default target is `114.66.24.221:49149`
  - default file path is `/flag`
  - the service reset on a later reconnection, but the first exploit run succeeded and returned the flag
- Verified remote flag: `nctf{4n_1N73R3571n9_U53_OF_FuNc71on_P7r}`
