# Headless IDA Export

Use `python scripts/export_headless_pseudocode.py /path/to/binary` whenever a local challenge binary is available.

The wrapper:

- runs `idat` with `TVHEADLESS=1`, with legacy `idat64` fallback for older installs
- calls `INP.py` from IDA-NO-MCP
- first honors `CTF_PWN_IDAT_PATH` and `CTF_PWN_IDA_NO_MCP_PATH` when they are set
- reuses a complete export if it is newer than the binary and `INP.py`
- defaults to `full` profile, which keeps `memory/`

Default locations:

- export directory: next to the binary under `export-for-ai/<binary-name>-<sha256_8>/`
- cache directory: next to the binary under `.ctf-pwn-idat/<binary-name>-<sha256_8>/`
- fallback: `/tmp/ctf-pwn-idat/...` when the binary directory is not writable

Read the export in this order:

1. `function_index.txt` for navigation
2. `decompile/*.c` for function logic and call relationships
3. `strings.txt`, `imports.txt`, `exports.txt` for naming and reachability hints
4. `memory/` only when raw bytes materially help with exploitability
5. `decompile_failed.txt` to spot imported stubs or decompiler blind spots

When the wrapper fails:

- read the reported `idat.log`
- record whether the failure is loader, decompiler, or file-permission related
- continue with `objdump`, `readelf`, and debugger evidence instead of blocking
