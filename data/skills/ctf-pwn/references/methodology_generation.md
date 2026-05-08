# Post-Challenge Methodology Generation

Create a methodology note after every completed challenge. The goal is to preserve the decisive exploit insight, the failed routes worth remembering, and the exact signals that should trigger reuse later.

## Output Location

Save each note as:

`methodologies/{challenge_slug}_{date}.md`

Example:

`methodologies/babystack_2026-03-21.md`

## Required Follow-Up

After writing the methodology note:

1. Add one row to `methodologies/index.md`.
2. Update `patterns.md` only if the lesson generalizes across challenges.
3. Keep challenge-specific offsets, addresses, hosts, and ad hoc payload bytes inside the methodology note, not inside `patterns.md`.

## What Counts as Reusable

Promote something for future reuse only when it answers one of these:

- What signal should make future analysis start in a different place?
- What mitigation mix changes the preferred exploit route?
- What dead end was predictable and should be avoided next time?
- What leak or primitive-conversion trick is likely to recur?

## Methodology Template

```markdown
# CTF Pwn Methodology: {challenge_name}

**Date**: {date}
**Binary**: {binary_name}
**Architecture**: {arch}
**Mitigations**: {nx, pie, relro, canary, fortify, seccomp}
**Vulnerability Class**: {stack overflow / fmt / uaf / ...}
**Primitives**: {leak, partial overwrite, arbitrary write, orw, ...}
**Reuse Tags**: {comma-separated canonical tags}
**User-Provided ida-no-mcp Pseudocode**: {yes/no}

## 1. Snapshot

- Challenge goal and flag path assumptions
- Local artifacts used: binary, libc, loader, Dockerfile, patch
- Remote endpoint or runtime quirks

## 2. Ground Truth

- Triage facts from `file`, `checksec`, `readelf`, `objdump`, `strings`, `ldd`
- Exact bug evidence from disassembly or runtime
- What the debugger proved that pseudocode alone could not prove

## 3. Exploit Chain

- Vulnerability trigger and controllable data
- Offsets, leaks, and mitigation bypass sequence
- Final route: `ret2win`, `ret2libc`, `rop`, `orw`, heap route, `srop`, `fsop`, or other
- Decisive insight: one sentence describing the turning point

## 4. Dead Ends Worth Remembering

- Route attempted
- Why it failed
- What earlier signal should have warned about the failure

## 5. Lessons to Reuse

- Signals that should make future you think of this challenge
- Which mitigation mix made the chosen route correct
- Reusable helper functions, leak order, or primitive-conversion trick
- Should `patterns.md` be updated: yes or no, and with what generalized lesson

## 6. Deliverables

- Exploit path or script name
- Remote-specific adjustments
- Remaining assumptions or things not fully verified
```

## Index Row Format

Append one table row to `methodologies/index.md` with:

- `challenge`
- `arch`
- `mitigations`
- `vuln_class`
- `primitives`
- `decisive_insight`
- `reuse_tags`
- `file`

Keep `reuse_tags` comma-separated and limited to the canonical tags from `patterns.md`.
