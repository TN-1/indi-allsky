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
        logger.debug(f"PTY: Resized to {row}x{col}")
    except Exception as e:
        logger.error(f"PTY: set_winsize error: {e}")

def register_terminal_events(socketio):
    logger.info("PTY: REGISTERING HANDLERS MANUALLY...")

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
                        socketio.emit("pty-output", {"output": output}, namespace="/pty")
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

    def pty_connect(auth=None):
        sid = getattr(request, 'sid', 'unknown')
        logger.info(f"PTY: CONNECT namespace=/pty SID={sid} auth={auth}")
        
        if terminal_state.get("child_pid"):
            try:
                os.kill(terminal_state["child_pid"], 0)
                logger.info(f"PTY: Reusing existing PID {terminal_state['child_pid']}")
                if not terminal_state["background_task_started"]:
                    terminal_state["background_task_started"] = True
                    socketio.start_background_task(target=read_and_forward_pty_output)
                
                if terminal_state["fd"]:
                    os.write(terminal_state["fd"], b"\n")
                return
            except OSError:
                logger.info("PTY: Process is dead, cleaning up")
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

    def pty_input(data):
        logger.debug(f"PTY: INPUT received")
        fd = terminal_state.get("fd")
        if fd:
            try:
                os.write(fd, data["input"].encode())
            except OSError as e:
                logger.error(f"PTY: Write error: {e}")

    def pty_resize(data):
        logger.info(f"PTY: RESIZE received: {data}")
        fd = terminal_state.get("fd")
        if fd:
            set_winsize(fd, data["rows"], data["cols"])

    def pty_ping():
        sid = getattr(request, 'sid', 'unknown')
        logger.info(f"PTY: PING received SID={sid}")
        socketio.emit("pong", namespace="/pty")

    def pty_disconnect():
        sid = getattr(request, 'sid', 'unknown')
        logger.info(f"PTY: DISCONNECT SID={sid}")

    def global_connect():
        sid = getattr(request, 'sid', 'unknown')
        logger.info(f"GLOBAL CONNECT SID={sid}")

    # Register handlers manually without decorators
    socketio.on_event("connect", global_connect)
    socketio.on_event("connect", pty_connect, namespace="/pty")
    socketio.on_event("disconnect", pty_disconnect, namespace="/pty")
    socketio.on_event("pty-input", pty_input, namespace="/pty")
    socketio.on_event("resize", pty_resize, namespace="/pty")
    socketio.on_event("ping", pty_ping, namespace="/pty")

    logger.info("PTY: ALL HANDLERS REGISTERED MANUALLY")
