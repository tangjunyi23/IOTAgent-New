# CTF Pwn Pattern Library

Use this file after binary triage. Match the current challenge by `reuse_tags`, mitigation picture, and primitive. Add entries only when the lesson transfers across multiple challenges.

## Canonical Tags

Use these tags in `methodologies/index.md` and methodology notes:

- `stack-overflow`
- `fmt`
- `uaf`
- `double-free`
- `heap-overflow`
- `off-by-one`
- `ret2libc`
- `rop`
- `canary-bypass`
- `pie-leak`
- `seccomp`
- `srop`
- `fsop`
- `tcache`
- `signed-index`
- `orw`
- `cmd-injection`

## Promotion Rule

Promote a lesson into this file only if it changes how you would approach a future binary. Do not add challenge-specific offsets, one-off gadget addresses, or host-specific quirks.

## `stack-overflow` -> `ret2win` / `ret2libc` / `rop`

- Signals:
  - Fixed-size stack buffer fed by `read`, `gets`, `fgets`, `scanf("%s")`, `strcpy`, or equivalent loops
  - Crash or partial control near saved `RIP` or `RBP`
  - User-provided pseudocode or disassembly shows a write whose upper bound exceeds the local object size
- Primitive:
  - Return-address control or saved-frame corruption
- Route:
  - Try `ret2win` first
  - Switch to `ret2libc` when libc control is easier than gadget-heavy ROP
  - Use `open/read/write` when a shell is blocked or unnecessary
- Verify with:
  - cyclic offset, stack alignment, calling convention, and whether a canary must be leaked first
  - in fork servers, whether you can stop the overwrite inside saved `rbp`; if so, brute saved `rbp` byte-by-byte exactly like a canary by keeping the untouched suffix intact and using the success or crash distinction as the oracle
- Add to the library when:
  - the reusable lesson is a recognizable cue such as a menu echo leaking a canary before the overflow, or a short read loop allowing staged ROP
  - the decisive trick is converting a tiny socket `read` into a full ret2libc by rewriting that active call's return address and pacing each chunk to avoid TCP short-read desynchronization
  - a leak or fake-frame stage temporarily abuses the executable's copy-relocated `stdin` or `stdout` globals; once a later `read` lands there, treat stdio as poisoned and finish with raw `read@plt`, `execve`, or `orw` instead of planning around later `puts` or `printf`
  - the decisive trick is restoring the caller's frame pointer and re-entering a mid-function caller block that already loads arguments from caller locals; overwriting those caller locals can turn an existing response helper into a leak primitive without needing a full `write(fd, addr, len)` gadget chain

## `fmt` -> leak-first or arbitrary-write

- Signals:
  - `printf`, `fprintf`, `dprintf`, `syslog`, or wrappers where attacker input controls the format string
  - Stack leaks or `%n` writes can be validated at runtime
  - Pseudocode claims a format-string issue, but the register or stack argument order must still be confirmed in disassembly
  - A filename or path buffer is populated through `snprintf(dst, size, user_fmt)` before `open` or `fopen`
- Primitive:
  - Stack or libc leak, arbitrary read through `%s`, or arbitrary write through `%n`
  - Format-string-driven path synthesis through stack-resident startup strings such as `argv[0]`
- Route:
  - Leak PIE, canary, or libc first
  - Use writes only after the stack index and byte count behavior are stable
  - Prefer GOT or hook writes only when RELRO and allocator state allow it
  - If the formatted output is later used as a filename, probe deeper positional `%s` indices early; recovering the missing ELF through `argv[0]` or nearby startup strings is often shorter than building a blind write primitive
- Verify with:
  - exact argument index, short versus wide writes, null-byte behavior, and line-buffering side effects
- Add to the library when:
  - you discover a repeatable stack-indexing trick, write-order pattern, or leak-minimization technique that generalizes

## `cmd-injection`

- Signals:
  - attacker-controlled text is converted into a shell command string before an allowlist check finishes
  - a signed parsed length is sign-extended and then compared with an unsigned jump such as `jbe` or `ja`
  - a global or shared command buffer is updated with `memcpy(..., strlen(src))`, `strncpy`, or equivalent code that can leave stale bytes after a shorter rewrite
  - attacker-controlled text is interpolated into an external helper DSL such as `sed`, `awk`, or `find` without escaping delimiter or flag syntax; the dangerous parser may be the helper itself rather than the shell
- Primitive:
  - staged shell-command injection through a preserved suffix or prefix in a reused command buffer
  - parser-level command execution by breaking out of an unescaped helper expression and reaching an execution feature such as GNU sed's `e` flag
- Route:
  - prove the length bypass first with a negative or wrapped value
  - confirm the copy order: command-buffer write before allowlist, then execution on a later request
  - build a two-step exploit: plant a long shell tail, then trigger the short allowlisted path that reuses the stale bytes
  - under tight path parsers, remember that `;`, `&&`, tabs, globs, and shell expansions can be enough even when literal spaces or slashes are filtered
  - if the target uses a helper like `sed 's#...#...#'`, switch mental models from shell injection to parser injection: try delimiter-breaking replacements and helper-specific execution flags before concluding that metacharacter filtering made the sink safe
- Verify with:
  - exact disassembly order of parse, length check, command synthesis, allowlist comparison, and execution
  - whether the reused buffer is zero-initialized only once and whether the shorter second write omits the NUL terminator
  - whether the helper is invoked through `execve`-style direct argument passing; if so, shell filters may be irrelevant while the helper's own expression grammar remains exploitable
- Add to the library when:
  - the transferable lesson is that a stale command suffix can survive a later allowlisted rewrite and convert a "safe" helper like `popen()` into a reliable command-execution primitive
  - the transferable lesson is that unescaped delimiter injection inside helper expressions can reach parser-native execution features such as GNU sed's `e` flag and yield reflected command output without any shell metacharacters

## `pie-leak` / `canary-bypass`

- Signals:
  - The main primitive exists, but direct hijack is blocked by PIE, ASLR, or stack canaries
  - Output functions echo stack or code pointers
  - A retry loop, fork server, or repeated menu lets you stage leaks before the final smash
- Primitive:
  - Reliable disclosure of canary, binary base, libc base, or stack pointer
- Route:
  - Convert the challenge into leak -> compute -> final overwrite
  - Prefer single-packet leak chains when alarms or one-shot exits exist
- Verify with:
  - leaked value shape, page alignment, symbol offset math, and whether the same process survives to the second stage
- Add to the library when:
  - the key reusable insight is how a supposedly harmless echo, banner, or error path becomes a mitigation bypass

## `signed-index`

- Signals:
  - An index parsed as signed `int` or `long` is only checked against an upper bound such as `idx <= max`
  - Disassembly keeps the signed value live into a scaled address like `[base + idx*8]` or `[base + idx*4]`
  - The indexed arrays sit near GOT slots, relocation-generated pointers, module tables, or other high-value writable metadata
- Primitive:
  - Negative-index OOB read or write into adjacent globals
  - Bootstrap arbitrary write when one reachable slot already contains a writable self-pointer or another useful in-module pointer
- Route:
  - Compute negative indices for every nearby target before going deeper on heap tricks
  - Prefer destinations that dereference into writable `.data/.bss`, then use that first write to seed a cleaner second-stage arbitrary write
  - In shared objects, pay special attention to `R_X86_64_RELATIVE` self-pointers and module tables because they often survive relocation as stable writable pointers
- Verify with:
  - the exact signed compare (`jg`, `jle`, etc.) and whether there is any hidden lower-bound check
  - the real symbol layout around the indexed arrays, not just pseudocode names
  - whether request- or process-persistent globals let you reset polluted state before the final overwrite
- Add to the library when:
  - the transferable lesson is that a missing lower-bound check on metadata indices beats allocator corruption and gives a shorter route into nearby function pointers or GOT state

## `heap-overflow` / `uaf` / `double-free` / `tcache`

- Signals:
  - Menu-driven alloc, edit, show, and free actions
  - Pointer reuse, stale references, size confusion, or missing nulling after `free`
  - Disassembly or pseudocode suggests chunk overlap or freelist corruption, but allocator version still matters
- Primitive:
  - Overlapping chunks, poisoned freelist, arbitrary allocation target, or use-after-free type confusion
- Route:
  - Start from the simplest consequence: leak, overlap, arbitrary write
  - Map glibc version before choosing fastbin, tcache, unlink, or hook-based routes
  - Prefer stable `__free_hook`, vtable, or function-pointer targets only when the version and hardening permit them
- Verify with:
  - chunk sizes after alignment, bin placement, safe-linking state, and whether the target binary ships its own libc
- Add to the library when:
  - the lesson is allocator-behavior driven and will change how you inspect future heap menus
  - for CPython or other interpreter-object corruption, a stale raw pointer plus a later builtin call site may be easier to exploit by rewriting a code object’s `co_names` tuple entry to an existing name object such as `eval`, instead of trying to patch dict key tables or lower-heap hash metadata first

## `off-by-one`

- Signals:
  - Copy loops with `<=`, newline stripping, fencepost null termination, or size-minus-one confusion
  - Heap chunk size or adjacent metadata changes by one byte
  - Stack overwrite reaches saved frame data but not a full return address
- Primitive:
  - Partial pointer overwrite, chunk-size corruption, null-byte poisoning, or frame-chain pivot
- Route:
  - Look for least-significant-byte control, top-chunk or size-field abuse, and partial GOT or return-slot edits
  - Pair with a leak if ASLR makes the partial overwrite ambiguous
- Verify with:
  - exact byte written, sign of the byte, and whether null-byte semantics help or hurt
- Add to the library when:
  - the insight is a generic fencepost pattern rather than a one-off offset

## `seccomp` / `orw`

- Signals:
  - Syscall filter present, shell spawns fail, or remote IO is jailed
  - Binary exposes readable file paths, open-like helpers, or straightforward read and write gadgets
- Primitive:
  - Code-execution path exists, but `execve` is blocked
- Route:
  - Build `open/read/write` first
  - Reuse libc wrappers when raw syscalls are filtered inconsistently
  - Prefer flag exfiltration over shell interactivity
- Verify with:
  - actual filter behavior, allowed syscalls, working file paths, and writable buffers for staged reads
- Add to the library when:
  - the lesson changes route selection for future sandboxed binaries

## `srop` / `fsop`

- Signals:
  - Standard ROP is cramped, but a `syscall; ret` gadget or controllable `_IO_FILE` state exists
  - Signal frames or libc FILE structures are attacker-influenced
- Primitive:
  - Full register control through forged signal frames, or control-flow/data-flow via FILE structure corruption
- Route:
  - Reach for these only when shorter routes are blocked
  - Keep the exploit explanation explicit because these routes are easy to cargo-cult incorrectly
  - If a later code path calls `fread` or a similar stdio read on an attacker-controlled `FILE*`, consider a fake `_IO_file_jumps` object with `_fileno = 0` and chosen `_IO_buf_base/_IO_buf_end`; this can turn the pending stdio call into a direct `read(0, target, len)` that overwrites GOT or `.bss` without needing a wide-vtable function-pointer pivot
- Verify with:
  - exact libc version, structure layout, gadget availability, and whether the target survives enough steps
- Add to the library when:
  - the transferable lesson is the precondition checklist, not the final payload bytes

## False Friends to Re-Check

- Pseudocode buffer sizes can be wrong; verify stack slots or heap sizes in disassembly or the debugger.
- A large `read` is not automatically exploitable if earlier bounds clamp the size at runtime.
- Hand-rolled or branchless `abs()` logic is not a real clamp until you test `INT_MIN`; if a later loop uses unsigned comparisons, that single edge case can reopen an oversized read or write.
- A format-looking bug is not real until the attacker actually controls the format argument.
- A shell string does not mean `system("/bin/sh")` is the right route; seccomp and IO constraints may make `orw` simpler.
- A printed `/bin/sh` string or reassuring win message is not enough; verify the exact pointer passed to `system()` or `exec*()`, because decoy helpers may call a harmless command such as `ls` instead.
- Heap notes without the correct libc version are often noise.
- Stream sockets can short-read staged payloads; if your exploit depends on many consecutive `read` lengths lining up exactly, pace or synchronize each chunk instead of bulk-sending the whole chain.
- Buffered request readers can consume queued post-exploit input before your shell ever starts; when targeting `system`, consider embedding the command string in the same overflowed buffer instead of pre-sending socket commands.
