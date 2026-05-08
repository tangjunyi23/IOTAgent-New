# CTF Pwn Methodology: orangeforce

**Date**: 2026-04-07
**Binary**: pwn
**Architecture**: x86_64
**Mitigations**: NX, PIE, Full RELRO, Canary
**Vulnerability Class**: heap overflow plus OOB heap read
**Primitives**: heap leak, libc leak, House of Force, arbitrary top-chunk relocation, libc hook overwrite, constrained shell
**Reuse Tags**: heap-overflow, ret2libc
**User-Provided ida-no-mcp Pseudocode**: no

## 1. Snapshot

- Menu challenge with character creation, repeated heap allocations for "powers", and a 64-byte OOB viewer.
- Local artifacts used: `pwn`, bundled `libc-2.27.so`, and `ld-2.27.so`.
- The first endpoint rotated; the exploit that solved the live target used `8.147.132.32:40772`.
- Flag recovered: `flag{7c3a2fec-5d3c-4a2b-b5c9-af2ea7abe951}`.

## 2. Ground Truth

- `Create a Power` does `malloc(size)` and then `read(0, ptr, size + 8)`, giving a controllable 8-byte heap overflow on every allocation.
- `View Your Powers` does `write(1, ptr, 0x40)`, so every power chunk is also a fixed 64-byte OOB read.
- The name buffer is heap-allocated with `read(0, name, 0x14)` and later printed with `%s` without forced NUL termination; this leaks past the end of the name and reveals the first power pointer from the adjacent heap layout.
- House of Force is the natural route on glibc 2.27 because there is no free primitive, but the 8-byte overflow is enough to:
  - forge the initial top size so a `sysmalloc` path is forced,
  - leak `main_arena+0x60` from the reused old-top chunk, and
  - rewrite the new top size to a huge odd value for arbitrary top-chunk relocation.
- Runtime testing proved the remote service mixes `scanf("%llu")` and raw `read(0, ...)` on a socket, so payload bytes sent too early can be consumed by stdio buffering, and large writes can also short-read at TCP packet boundaries.

## 3. Exploit Chain

- Allocate a `0x10` power with an `0x18` payload to create the first overflow and use `view_char()` to leak `p0`.
- Compute `old_top = p0 + 0x30`, then overflow the next chunk so the top size becomes the page-aligned distance to the next page boundary with `PREV_INUSE` set.
- Request `0xd68` bytes to force `sysmalloc`, but send `b"\\t" * 0xd68 + p64(0x0909090909090909)` after the exact `Power: ` prompt:
  - the tabs stop remote desync because any residual bytes are whitespace to later `scanf("%d")`,
  - `0x0909090909090909` is a huge valid odd top size, so it replaces the old local `-1` write without leaving hostile non-whitespace tail bytes.
- Read power index 1 and recover `libc_base = leak_qword - 0x3ebca0` from the unsorted-bin `main_arena+0x60` pointer at offset `0x20`.
- Recompute the post-`sysmalloc` top as `old_end + 0x1f000 + request2size(0xd68)`, then use House of Force again to move top to `__malloc_hook - 0x10`.
- The decisive remote adjustment was to spray `p64(one_gadget)` across the first `0x200` bytes of the landing chunk instead of writing a single qword, because small allocator-placement skew still left the hook region inside that sprayed window.
- Trigger one more `malloc(1)` and use the spawned `/bin/sh` to read `/flag`.
- Decisive insight: on a socket-backed `scanf` + `read` heap service, make any potentially residual bytes whitespace-compatible first; once the remote stops desynchronizing, ordinary House of Force math plus a small hook spray is enough to finish the glibc-2.27 route.

## 4. Dead Ends Worth Remembering

- Sending the `0xd68` trigger payload eagerly right after the size
  - Failed because `scanf("%llu")` could pre-buffer part of the payload, and the later raw `read` then saw a short count before the final 8-byte top overwrite arrived.
  - Earlier signal: the service started printing repeated `Power X Created` and `Your powers is overflown!`, which means stale bytes were being reinterpreted as later menu input.

- Using non-whitespace filler such as `b"D" * 0xd68`
  - Failed because any short-read residue became hostile input for the next `scanf("%d")`, which kept stale menu state at choice 3 and walked the menu loop out of sync.
  - Earlier signal: after the big allocation, sending menu choice 4 produced `Size: Power: Power 4 Created...` instead of `Index for Power:`.

- Writing only one `one_gadget` qword at the predicted hook slot
  - Failed intermittently on the remote target even when the chunk contents were correct-looking, because the landing region was close but not stable enough to trust a single 8-byte write.
  - Earlier signal: viewing the final power showed the intended bytes, but the next `malloc(1)` still continued normally and printed `Power:`.

## 5. Lessons to Reuse

- When a challenge mixes stdio parsing with raw `read()` on a socket, treat "safe residual bytes" as part of the exploit design. Whitespace payloads can be the difference between a usable and unusable remote exploit.
- If a House of Force route only needs the final 8-byte overwrite to be "very large and odd", choose bytes that are also benign to any accidental later parser, not just the numerically largest value.
- For hook-target House of Force on a flaky remote, a short sprayed overwrite around the predicted hook slot is often cheaper than re-deriving every allocator constant under network noise.
- Should `patterns.md` be updated: no. The reusable lesson is real, but it is best kept as a challenge-specific note about socket I/O desync in `scanf` + `read` services rather than a new canonical pattern entry.

## 6. Deliverables

- Exploit script: `/home/tankuku/timu/pwn/orangeforce/exploit.py`
- Remote-specific adjustments:
  - wait for the exact `Power: ` prompt before the `0xd68` stage,
  - use tab filler plus `0x0909090909090909` for the post-`sysmalloc` top overwrite,
  - spray the final `one_gadget` across the hook landing chunk,
  - read `/flag` directly instead of redirecting stderr to `/dev/null`, because the remote shell environment rejected that redirection.
- Remaining assumptions:
  - the core exploit path is proven and the flag was recovered,
  - the saved `exploit.py` was updated with the working remote adjustments, but the most reliable flag recovery during solving still came from the explicitly instrumented one-shot run rather than a long unattended retry loop.
