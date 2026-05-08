#!/usr/bin/env python3

from pwn import *

# Usage:
#   python3 exp.py
#   python3 exp.py GDB
#   python3 exp.py REMOTE HOST=host PORT=31337
#   python3 exp.py GDB GDBPORT=31338
#
# This skeleton keeps pwntools IO and GDB control in separate tubes without
# using pwntools.gdb.attach() or pwntools.gdb.debug().

BIN = "./chall"
HOST = args.HOST or "127.0.0.1"
PORT = int(args.PORT or 31337)
GDB_HOST = "127.0.0.1"
GDB_PORT = int(args.GDBPORT or 31338)

context.binary = ELF(BIN, checksec=False)
context.log_level = args.LOG_LEVEL or "info"

GDB_BASE_SCRIPT = """
set pagination off
set confirm off
set sysroot /
set breakpoint pending on
set print thread-events off
set disassemble-next-line on
handle SIGALRM nostop noprint pass
handle SIGPIPE nostop noprint pass
"""

GDB_SCRIPT = """
break *main
continue
"""


def _script_lines(script):
    lines = []
    for raw in script.splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            lines.append(line)
    return lines


class GdbController:
    def __init__(self, exe_path, host, port, base_script, extra_script):
        self.exe_path = exe_path
        self.host = host
        self.port = port
        self.base_script = base_script
        self.extra_script = extra_script
        self.io = None

    def start(self):
        argv = ["gdb", "-q", "-nx", self.exe_path]
        for line in _script_lines(self.base_script):
            argv += ["-ex", line]
        argv += ["-ex", "target remote {}:{}".format(self.host, self.port)]
        for line in _script_lines(self.extra_script):
            argv += ["-ex", line]
        self.io = process(argv, stdin=PTY, stdout=PTY, stderr=STDOUT)
        return self

    def wait_for_prompt(self, timeout=1):
        return self.io.recvuntil(b"(gdb) ", timeout=timeout)

    def cmd(self, command, timeout=1):
        self.io.sendline(command.encode())
        return self.wait_for_prompt(timeout=timeout)

    def continue_nowait(self):
        self.io.sendline(b"continue")

    def interrupt(self, timeout=1):
        self.io.send(b"\x03")
        return self.wait_for_prompt(timeout=timeout)

    def close(self):
        if self.io is None:
            return
        if self.io.poll() is None:
            self.io.sendline(b"quit")
            self.io.close()


def _strip_gdbserver_chatter(io):
    prefixes = (
        b"Process ",
        b"Listening on port ",
        b"Remote debugging from host ",
        b"Attached; pid = ",
    )

    while True:
        line = io.recvline(timeout=0.05)
        if not line:
            return
        if line.startswith(prefixes):
            continue
        io.unrecv(line)
        return


def start_local(argv=None, gdb_script=GDB_SCRIPT):
    argv = argv or []

    if not args.GDB:
        return process(
            [context.binary.path] + argv,
            stdin=PTY,
            stdout=PTY,
            stderr=STDOUT,
        ), None

    gdbserver_argv = ["gdbserver", "--once"]
    if args.NOASLR:
        gdbserver_argv.append("--disable-randomization")
    else:
        gdbserver_argv.append("--no-disable-randomization")
    gdbserver_argv += [
        "{}:{}".format(GDB_HOST, GDB_PORT),
        context.binary.path,
    ] + argv

    io = process(
        gdbserver_argv,
        stdin=PTY,
        stdout=PTY,
        stderr=STDOUT,
    )
    io.recvuntil("Listening on port {}".format(GDB_PORT).encode())
    dbg = GdbController(
        context.binary.path,
        GDB_HOST,
        GDB_PORT,
        GDB_BASE_SCRIPT,
        gdb_script,
    ).start()
    _strip_gdbserver_chatter(io)
    return io, dbg


def start_remote():
    if args.GDB:
        log.warning("Ignoring GDB in REMOTE mode; use local replay or a separate remote gdbserver setup.")
    return remote(HOST, PORT), None


def start(argv=None, gdb_script=GDB_SCRIPT):
    argv = argv or []
    if args.REMOTE:
        return start_remote()
    return start_local(argv, gdb_script=gdb_script)


def main():
    io, dbg = start()

    if dbg is not None:
        log.info("Initial GDB stop:")
        log.info(dbg.wait_for_prompt(timeout=2).decode(errors="ignore"))
        log.info(dbg.cmd("x/i $pc").decode(errors="ignore"))
        log.info(dbg.cmd("info registers").decode(errors="ignore"))
        dbg.continue_nowait()

    io.interactive()


if __name__ == "__main__":
    main()
