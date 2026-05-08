# CTF Pwn Methodology: encryption

**Date**: 2026-04-04
**Binary**: `main`
**Architecture**: `x86_64`
**Mitigations**: `NX`, `Partial RELRO`, `No PIE`, `No Canary`, `SHSTK`, `IBT`, `No seccomp observed`
**Vulnerability Class**: `input-first chosen-plaintext oracle with same-second key reuse and an irrelevant stack overflow`
**Primitives**: same-second chosen-plaintext oracle, parallel basis sampling, affine GF(2) matrix recovery, direct blockwise decryption
**Reuse Tags**: `stack-overflow`
**User-Provided ida-no-mcp Pseudocode**: `no`

## 1. Snapshot

- Goal: recover the remote flag from `114.66.24.221:33171`.
- Artifacts used: local stripped ELF `main`, pwntools scripts, and the live remote oracle.
- Runtime quirks:
  - the service does not print a banner until after it receives one line of input;
  - reconnecting multiple times within the same `time(NULL)` second reuses the exact same cipher state;
  - the binary also has a `gets()` overflow and a hidden `system("su ctf -s /bin/sh")` helper, but that was a dead end for the remote solve.

## 2. Ground Truth

- `main` is a non-PIE amd64 ELF with `NX`, `Partial RELRO`, `No Canary`, `SHSTK`, and `IBT`.
- The program seeds `srand(time(NULL))`, fills a 16-byte seed with `rand() % 256`, calls external `init(ctx, seed)`, encrypts one user-chosen plaintext, then encrypts the flag with the same initialized context.
- The obvious bug is real:
  - `gets(local_3e8)` reads into a 64-byte stack buffer,
  - the length check happens later via `strlen(local_3e8)`,
  - embedded `\x00` bytes bypass the `> 64` check while still overflowing into `ctx` and saved control data.
- Remote oracle evidence mattered more than the decompiler:
  - sending input immediately, not waiting for a banner, was required to get output;
  - repeated connections within one second returned identical ciphertexts for the same plaintext and identical flag ciphertexts, proving same-second key reuse;
  - identical 16-byte plaintext blocks produced identical ciphertext blocks, so the cipher works independently per 16-byte block;
  - a same-second four-point test on `0xff^16` plus bit-flipped variants satisfied `E(x^y) ^ E(b) == (E(x)^E(b)) ^ (E(y)^E(b))`, proving the first-block transform is affine over GF(2).

## 3. Exploit Chain

- Treat the first 16-byte ciphertext block as an affine map `E_t(P) = M * P xor k_t`, where:
  - `M` is constant across all runs,
  - `k_t` changes once per second with the `time(NULL)` seed.
- Use a printable nonzero baseline block `B = 0xff * 16`, then for each input bit position `i` query `B xor e_i` within the same second.
- Because `E_t(B xor e_i) xor E_t(B) = M * e_i`, the 128 basis queries recover all 128 columns of `M`.
- Batch the basis collection in parallel:
  - 16 bit-flips plus one baseline per second,
  - 8 seconds total to recover all 128 columns,
  - reject any batch whose returned flag ciphertexts are not identical, because that means the threads crossed a second boundary.
- Invert `M` over GF(2) once.
- On a fresh connection, query the baseline block `B` again:
  - derive `k_t = E_t(B) xor M * B`,
  - split the returned flag ciphertext into 16-byte blocks,
  - decrypt each block with `P = M^{-1} * (C xor k_t)`,
  - remove PKCS#7 padding.
- Decisive insight: once the same-second oracle showed a stable affine block transform, the shortest route was not the `gets()` overflow but a matrix-recovery attack that turned the service into a solvable linear system.

## 4. Dead Ends Worth Remembering

- Ret2hidden-shell was tempting because `main` contains a helper that builds `su ctf -s /bin/sh`, and local testing showed the overflow can reach that function with a stack-alignment `ret`.
- That route was the wrong place to spend time:
  - the service is an input-first one-shot oracle, not a normal interactive shell service;
  - the overflow also corrupts the large external cipher context before control reaches the return site;
  - the real challenge is the cipher structure, not CET bypass or shell stabilization.
- Assuming the block function was plain XOR was also wrong. Some same-second differentials looked XOR-like on repeated-byte blocks, but mixed-byte blocks disproved that shortcut quickly.

## 5. Lessons to Reuse

- Signals to watch for:
  - a one-shot encryption service that reseeds from `time(NULL)` on every connection;
  - the ability to make many connections within the same second;
  - repeated-block ECB behavior plus a same-second affine-difference pattern.
- Mitigation picture:
  - classic binary mitigations were mostly noise here; the real primitive was the live oracle.
  - The presence of a genuine stack overflow can still be a trap if the crypto path gives a shorter, more reliable solve route.
- Reusable trick:
  - when a keyed block transform is affine per second, use a fixed nonzero baseline plus same-second bit-flip queries to recover the linear matrix and per-run offset separately.
- Should `patterns.md` be updated: no. The affine-matrix recovery route is powerful, but the exact "same-second reconnect oracle with per-second affine key offset" signal is still too specialized for the generic pattern file.

## 6. Deliverables

- Solver script: `/home/tankuku/timu/re/solve_encryption.py`
- Remote-specific adjustments:
  - target endpoint was `114.66.24.221:33171`
  - queries had to be launched in parallel and grouped by second
  - batches were validated by checking that every thread in the batch saw the same flag ciphertext
- Verified remote flag: `flag{f181d7dd-2302-4fd4-b4e3-cb0784877eb6}`
