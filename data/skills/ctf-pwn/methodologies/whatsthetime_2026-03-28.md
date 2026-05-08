# CTF Pwn Methodology: whatsthetime

**Date**: 2026-03-28
**Binary**: whatsthetime
**Architecture**: i386
**Mitigations**: NX, Partial RELRO, No PIE, No Canary
**Vulnerability Class**: stack overflow behind time-seeded XOR
**Primitives**: banner-derived XOR seed, encoded return-address overwrite, direct `ret2plt(system)`
**Reuse Tags**: stack-overflow, rop
**User-Provided ida-no-mcp Pseudocode**: no

## 1. Snapshot

- The service at `143.198.163.4:3000` prints a rounded current time, reads up to `0xa0` bytes, and echoes back `0x28` bytes before returning.
- Local artifacts used: the single ELF `whatsthetime`; no bundled libc or loader were provided.
- The remote host used UTC, so the printed `ctime()` banner mapped directly back to the seed without extra timezone adjustment.

## 2. Ground Truth

- `file`, `checksec`, and `readelf` showed a 32-bit dynamically linked ELF with NX enabled, partial RELRO, no PIE, and no canary.
- `read_user_input` allocates `0xa0` bytes on the heap, reads attacker input there, XOR-decodes it 4 bytes at a time with `seed`, `seed+1`, `seed+2`, ... , then `memcpy`s the full `read()` length onto a local stack buffer at `[ebp-0x40]`.
- The saved return address sits `0x44` bytes past that buffer, so any decoded input longer than `68` bytes controls `EIP`.
- `main` computes `seed` as the current Unix timestamp rounded down to the minute and prints that value with `ctime()`. The banner therefore leaks the exact XOR keystream origin.
- The disassembly of `win` disproved the obvious route: it prints `"/bin/sh"` in the status message but actually calls `system("ls")`, then prints `"oops wrong command"`.
- `.rodata` still contains a real `"/bin/sh"` string, and the binary imports `system@plt`, so a direct `ret2plt(system)` chain is available without libc leaks.

## 3. Exploit Chain

- Parse the banner after `Currently the time is: ` and convert the printed minute back to a Unix timestamp.
- Encode a stack payload by XORing each 4-byte chunk with little-endian `seed + chunk_index`.
- Overflow `read_user_input` with `0x44` bytes of padding, then `system@plt`, a dummy return address, and the `.rodata` pointer to `"/bin/sh"`.
- After the function returns, `system("/bin/sh")` runs on the same socket; send `pwd; ls -la; cat flag* /flag* /home/*/flag*` to exfiltrate the flag.
- Decisive insight: the minute banner fully reveals the XOR key, and the tempting `win()` function is bait because the actual useful route is `system@plt("/bin/sh")`, not `win()`.

## 4. Dead Ends Worth Remembering

- Route attempted: ret directly into `win`.
- Why it failed: the function only pretends to launch `/bin/sh`; the actual `system` argument is the neighboring `"ls"` string in `.rodata`.
- Earlier warning sign: the `system` call target must be confirmed from disassembly or runtime, not inferred from nearby strings or printed status text.

## 5. Lessons to Reuse

- If a service prints a rounded or derived time value before decoding input with a time-based key, treat that banner as a likely direct seed leak.
- On 32-bit non-PIE binaries with NX and no canary, `ret2plt(system)` plus an existing `"/bin/sh"` string is often shorter than chasing fake win helpers.
- When a challenge ships an attractive `win()` function, verify the exact pointer passed to `system()` or `exec*()` before committing to the route.
- Reusable helper: a chunk-wise XOR encoder that mirrors the binary's `seed + block_index` logic.
- Should `patterns.md` be updated: yes, add a false-friend reminder that a printed shell string or win message may not match the real command passed to `system()`.

## 6. Deliverables

- Exploit script: `/home/tankuku/timu/pwn/solve.py`
- Remote-specific adjustment: the script auto-parses the banner and can brute-force timezone offsets, though the challenge server used UTC.
- Remaining assumptions: the exploit assumes the service keeps stdin attached to the spawned shell long enough to send one command batch, which held locally and remotely.
