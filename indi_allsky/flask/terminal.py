import pty
import os
import select
import termios
import struct
import fcntl
import logging
import errno
import sys
from flask import request

# Global state
terminal_state = {
    "fd": None,
    "child_pid": None,
    "background_task_started": False
}

logger = logging.getLogger('indi_allsky')

def set_winsize(fd, row, col):
    try:
        winsize = struct.pack("HHHH", int(row), int(col), 0, 0)
        fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)
        logger.info(f"PTY: Winsize set to {row}x{col}")
    except Exception as e:
        logger.error(f"PTY: set_winsize error: {e}")

def register_terminal_events(socketio):
    logger.info("PTY: REGISTERING EXPLICIT DEFAULT NAMESPACE HANDLERS...")

    def read_and_forward_pty_output():
        max_read_bytes = 1024 * 20
        logger.info("PTY: Starting output background task")
        while True:
            socketio.sleep(0.01)
            fd = terminal_state.get("fd")
            if fd:
                try:
                    (data_ready, _, _) = select.select([fd], [], [], 0)
                    if data_ready:
                        output = os.read(fd, max_read_bytes).decode(errors="ignore")
                        socketio.emit("pty-output", {"output": output}, namespace="/")
                except Exception as e:
                    logger.error(f"PTY: Read error: {e}")
                    terminal_state["fd"] = None
                    terminal_state["child_pid"] = None
                    terminal_state["background_task_started"] = False
                    break
            else:
                logger.info("PTY: FD is None, stopping background task")
                terminal_state["background_task_started"] = False
                break

    @socketio.on("connect", namespace="/")
    def on_connect(*args, **kwargs):
        sid = getattr(request, 'sid', 'unknown')
        logger.info(f"PTY: CONNECT namespace=/ SID={sid}")
        
        if terminal_state.get("child_pid"):
            try:
                os.kill(terminal_state["child_pid"], 0)
                logger.info(f"PTY: Reusing PID {terminal_state['child_pid']}")
                if not terminal_state["background_task_started"]:
                    terminal_state["background_task_started"] = True
                    socketio.start_background_task(target=read_and_forward_pty_output)
                
                if terminal_state["fd"]:
                    os.write(terminal_state["fd"], b"\n")
                return
            except OSError:
                terminal_state["child_pid"] = None
                terminal_state["fd"] = None

        try:
            logger.info("PTY: Forking new bash process")
            (child_pid, fd) = pty.fork()
        except Exception as e:
            logger.error(f"PTY: fork failed: {e}")
            return

        if child_pid == 0:
            os.execvp("/bin/bash", ["bash"])
        else:
            terminal_state["fd"] = fd
            terminal_state["child_pid"] = child_pid
            terminal_state["background_task_started"] = True
            set_winsize(fd, 24, 80)
            socketio.start_background_task(target=read_and_forward_pty_output)
            logger.info(f"PTY: FORKED BASH PID {child_pid}")

    @socketio.on("pty-input", namespace="/")
    def on_input(data):
        logger.info("PTY: INPUT received")
        fd = terminal_state.get("fd")
        if fd:
            try:
                os.write(fd, data["input"].encode())
            except OSError as e:
                logger.error(f"PTY: Write error: {e}")

    @socketio.on("resize", namespace="/")
    def on_resize(data):
        logger.info(f"PTY: RESIZE received: {data}")
        fd = terminal_state.get("fd")
        if fd:
            set_winsize(fd, data["rows"], data["cols"])

    @socketio.on("ping", namespace="/")
    def on_ping():
        sid = getattr(request, 'sid', 'unknown')
        logger.info(f"PTY: PING received SID={sid}")
        socketio.emit("pong", namespace="/")

    @socketio.on_error_default
    def default_error_handler(e):
        logger.error(f"PTY: SOCKET ERROR: {e}")

    logger.info("PTY: EXPLICIT HANDLERS REGISTERED")
