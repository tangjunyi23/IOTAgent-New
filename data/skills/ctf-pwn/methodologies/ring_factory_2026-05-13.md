# CTF Pwn Methodology: ring_factory

**Date**: 2026-05-13
**Binary**: `pwn2`
**Architecture**: x86_64
**Mitigations**: NX, PIE, Full RELRO, Canary
**Vulnerability Class**: short format-string canary leak plus UAF and uninitialized heap leak plus stack overflow
**Primitives**: canary leak, heap leak, libc leak, ret2libc `system("/bin/sh")`
**Reuse Tags**: fmt, uaf, tcache, ret2libc, rop
**User-Provided ida-no-mcp Pseudocode**: no

## 1. Snapshot

- Menu challenge with four actions: show, forge, discard, and use sling rings.
- Local artifacts used: `attachment-49.zip`, extracted `pwn2`, bundled `libc-2.31.so`, and the exact Ubuntu glibc bundle recovered from `glibc-all-in-one` as `2.31-0ubuntu9.18_amd64`.
- Remote endpoint: `39.96.193.120:10006`.
- Flag recovered: `ISCC{ff9e0a07-1f89-44e9-a17c-838661b23dc3}`.

## 2. Ground Truth

- `main` reads a 6-byte name and then does `printf(s)`, so the initial prompt is a genuine format string, but the five-character payload budget only allows one small positional leak such as `%7$p`.
- Runtime probing showed `%7$p` is the current stack canary, which is exactly what the later `use_slingring` overflow needs.
- `use_slingring` asks for an id, ignores it, and then does `fgets(buf, 0x100, stdin)` into a stack region starting at `rbp-0x40` with the canary at `rbp-0x8`, so the saved canary is reached after `0x38` bytes.
- `forge_slingring` allocates `malloc(0x84)`, stores only the first destination byte at offset `0`, stores the amount at offset `0x80`, and leaves the rest of the chunk uninitialized.
- `discard_slingring` frees `rings[idx]` but never nulls the slot, and `show_slingrings` later prints both `rings[idx]` as `%s` and `*(int *)(rings[idx] + 0x80)`.
- That combination turns freed chunks into allocator-metadata oracles:
  - tcache entries leak heap pointers directly through the stale `%s`,
  - a non-top freed chunk in unsorted bin leaks `main_arena+0x60`, which was `libc_base + 0x1ecbe0` for `Ubuntu GLIBC 2.31-0ubuntu9.18`.
- The decisive runtime proof was freeing nine equal-size chunks with a guard allocation behind the target:
  - allocate slots `0..8`,
  - free `0..6` to fill tcache,
  - free `7` while `8` is still allocated so slot `7` goes to unsorted instead of consolidating with top,
  - call `show` and parse the raw bytes printed for slot `7`.

## 3. Exploit Chain

- Leak the canary with the only cheap initial format-string probe: `%7$p`.
- Allocate nine `0x84` rings and free the first eight in order so slot `7` becomes a dangling unsorted-bin chunk and leaks `main_arena+0x60`.
- Compute `libc_base = unsorted_leak - 0x1ecbe0`.
- Use option `4` and send a stack-smash payload:
  - `b"A" * 0x38`
  - leaked canary
  - dummy saved `rbp`
  - `ret`
  - `pop rdi; ret`
  - `"/bin/sh"` from libc
  - `system` from libc
- Queue `cat /flag` on the spawned shell.
- Decisive insight: the format string is too short to solve everything, so spend it only on `%7$p` for the canary and let the dangling fixed-size ring slots print allocator metadata; one guarded unsorted-bin free supplies the libc leak that completes the final `use_slingring` ret2libc.

## 4. Dead Ends Worth Remembering

- Trying to finish from the format string alone
  - Failed conceptually because a five-character payload can leak at most one useful stack slot, which is not enough for canary plus libc plus a control primitive.
  - Earlier signal: the name buffer length hard-caps the attack surface to one positional specifier.

- Freeing only eight rings and expecting slot `7` to leak libc
  - Failed because the last freed chunk was adjacent to top and consolidated instead of entering unsorted, so the stale string only showed the original user byte.
  - Earlier signal: the would-be unsorted slot kept its original first character and did not show the typical six-byte high-address leak pattern.

- Overcomplicating the heap route into a true double-free attack
  - Unnecessary and riskier under glibc 2.31 tcache checks; stale-slot reads already provide the only leak that the stack exploit is missing.
  - Earlier signal: `show` was already exposing raw freed-chunk pointers without any poisoning step.

## 5. Lessons to Reuse

- If a menu heap challenge stores only one byte of a heap string and later prints the whole chunk with `%s`, assume both uninitialized-chunk and freed-chunk metadata leaks are in play immediately.
- When one primitive is too narrow to bypass every mitigation, split roles deliberately: format string for canary, allocator metadata for libc, final overflow for control.
- If a same-size freed chunk should leak unsorted metadata but does not, check top-chunk adjacency first; one guard allocation can be the whole difference between a dead end and a clean libc leak.
- Should `patterns.md` be updated: no. The lesson is useful, but it is still best captured as a challenge-specific combination of a tiny format-string budget with stale-slot allocator leaks.

## 6. Deliverables

- Exploit path: one-shot pwntools ret2libc using `%7$p` plus an unsorted-bin UAF leak, run inline during solving.
- Remote-specific adjustments:
  - use the exact Ubuntu glibc bundle `2.31-0ubuntu9.18_amd64`,
  - keep a guard allocation after the unsorted target,
  - allow for noticeably slower remote menu pacing than the local process.
- Remaining assumptions:
  - no standalone exploit file was saved during the solve,
  - the final shell-based read verified the flag path directly as `/flag`.
