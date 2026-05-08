# CTF Pwn Methodology: interpreter

**Date**: 2026-03-28
**Binary**: interpreter
**Architecture**: x86_64
**Mitigations**: NX, No RELRO, No PIE, No Canary, static binary, RWX main segment
**Vulnerability Class**: out-of-bounds read and write in vector and string primitives against host-stack-allocated VM objects
**Primitives**: raw host-stack pointer recovery, host-stack OOB read/write, lambda-field corruption, ret2win via fake host stack
**Reuse Tags**: rop
**User-Provided ida-no-mcp Pseudocode**: no

## 1. Snapshot

- The service is a tiny threaded interpreter with bytecode opcodes equal to function addresses and immediates stored inline after each opcode.
- Local artifacts used: `interpreter`, `assembler.tar.gz`, `compiler.tar.gz`.
- Remote endpoint: `143.198.163.4:1900`.
- Headless IDA export was unavailable because the local wrapper reported `Cannot continue without a valid license`.
- Remote quirk observed on 2026-03-28: even a trivial `LOAD 0 ; DONE` payload returned zero bytes, so the local exploit path is validated but the remote instance did not expose stdout in the expected way during this solve.

## 2. Ground Truth

- `file`: 64-bit static stripped ELF.
- `checksec`: NX enabled, No PIE, No RELRO, No Canary, RWX segment present.
- The interpreter reads attacker-controlled bytecode into an anonymous mapping, flips that mapping read-only with `mprotect`, maps a second RW page for the VM stack, then enters the threaded loop by setting `rsp` to the bytecode and returning through opcode addresses.
- VM heap objects are not allocated in the RW VM stack mapping. They are allocated by subtracting from the saved host `rbp`, so vectors, strings, pairs, and lambdas all live on the native stack frame that called the interpreter.
- `vector-ref`, `vector-set!`, `string-ref`, and `string-set!` all load the container length into `rdi` but then compare the user index against the object base pointer in `rax` instead of the length:
  - `vector-ref`: `mov rdi, [rax]` then `cmp rcx, rax`
  - `vector-set!`: `mov rdi, [rax]` then `cmp rcx, rax`
  - `string-ref`: `mov rdi, [rax]` then `cmp rcx, rax`
  - `string-set!`: `mov rdi, [rax]` then `cmp rcx, rax`
- Because the comparison is against the object base address, any small nonnegative index is accepted and becomes a forward OOB read or write into higher host-stack addresses.
- `vector-set!` returns the untagged vector base pointer instead of the vector object. That turns a safe in-bounds update into a raw stack-pointer leak primitive.
- `lambda` stores its arity after an internal `sar rcx, 2`. Creating a lambda with a raw aligned integer on the stack therefore produces a reusable divide-by-four gadget by reading back the lambda's arity field through a later OOB vector read.

## 3. Exploit Chain

- Allocate a holder layout on the host stack:
  - `F`: empty vector
  - `L`: placeholder lambda whose offset field will be patched later
  - `H`: vector containing `[L, F]`
  - `V1`: one-element vector used as the first OOB gadget
- Use an in-bounds `vector-set!` on `V1[0]` to recover the raw base pointer of `V1`.
- Use `V1` OOB reads to recover:
  - the interpreter's saved `rbp` as `V1_base + 72`
  - the mapped bytecode base pointer from the caller's stack frame
  - `F` back out of `H`
- Compute `delta = fake_stack_target - code_base`, where `fake_stack_target` is the saved interpreter `rbp` slot on the host stack.
- Create `D1 = lambda(F, delta)`, then read `D1.arity` through a lower vector `V2` to get `delta >> 2`.
- Create `D2 = lambda(F, D1.arity)`, then read `D2.arity` through a lower vector `V3` to get `delta >> 4`, which is exactly the threaded lambda offset needed by `call`.
- Use `V3` OOB writes to:
  - patch `L.offset = D2.arity`
  - write `0x8008570` at the fake host-stack entry point
  - write `0x80087f4` as a fallback return target if `execve` fails
- Recover `L` from `H[0]` via `V3` OOB read and invoke it with arity zero.
- `call` switches `rsp` from the read-only bytecode mapping to the fake host stack, so the next `ret 8` lands in the hidden helper at `0x8008570`, which executes `execve("/bin/cat", ["/bin/cat", "flag.txt", NULL], NULL)`.
- Decisive insight: the shortest reliable route is to use `vector-set!` as a raw stack-pointer leak and use lambda-arity truncation twice as a built-in `>> 4`, turning the interpreter's own call mechanism into a host-stack ret2win.

## 4. Dead Ends Worth Remembering

- Directly overwriting the interpreter caller's saved return address was a dead end because normal completion goes through `DONE`, which restores `rsp`, calls the printer, and exits instead of returning through the original call site.
- Jumping straight to normal helper functions from the threaded code buffer was a dead end because the threaded dispatcher keeps `rsp` inside the read-only bytecode mapping, so ordinary prologues and `call` instructions fault when they try to push.
- Remote-only validation was inconclusive because the remote instance returned zero bytes even for a trivial `DONE` program, so lack of output was not enough to distinguish exploit failure from service-side fd wiring.

## 5. Lessons to Reuse

- When a custom VM allocates objects off the native `rbp`, any OOB container bug is immediately a host-stack bug, not just a VM-heap bug.
- If a setter returns an untagged base pointer, treat it as a pointer leak primitive even when the author probably meant to return the container.
- When the ISA lacks shifts but stores raw fields after `sar` or `shr` internally, object construction can act as a numeric conversion gadget.
- Threaded interpreters often keep `rsp` in nonstandard memory. Before trying ret2win, ask whether there is an existing VM path that will switch `rsp` back onto writable host memory for you.
- Should `patterns.md` be updated: no. The general lesson is useful, but it is still challenge-specific enough that the methodology note is the right place for it.

## 6. Deliverables

- Exploit script: `/home/tankuku/timu/pwn/exploit.py`
- Remote-specific adjustments: none in the final script; the validated path is the local host-stack ret2win. The remote service may need an fd-dup stage if it only exposes the socket on `fd 0`.
- Remaining assumptions:
  - The local and remote binaries are the same.
  - The host-stack frame layout around the interpreter entry is unchanged.
  - The remote no-output behavior is environmental, not a binary mismatch.
