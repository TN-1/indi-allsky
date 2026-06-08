import os
import json
import logging
import pty
import select
import termios
import struct
import fcntl
from pathlib import Path
from logging.config import dictConfig

from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_socketio import SocketIO

db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
socketio = SocketIO()

# Global state for terminal
terminal_state = {
    "fd": None,
    "child_pid": None,
    "background_task_started": False,
    "active_sid": None
}

from flask_login import LoginManager

from .views import bp_allsky  # noqa: E402
from .auth_views import bp_auth_allsky  # noqa: E402
from .syncapi_views import bp_syncapi_allsky  # noqa: E402
from .actionapi_views import bp_actionapi_allsky  # noqa: E402


dictConfig({
    'version' : 1,
    'formatters' : {
        'default' : {
            'format' : '[%(asctime)s] [%(levelname)s] %(processName)s-%(process)d %(module)s.%(funcName)s() [%(lineno)d]: %(message)s',
        },
        'syslog' : {
            'format' : '[%(levelname)s] %(processName)s-%(process)d %(module)s.%(funcName)s() [%(lineno)d]: %(message)s',
        },

    },
    'handlers' : {
        'wsgi' : {
            'class'     : 'logging.StreamHandler',
            'stream'    : 'ext://flask.logging.wsgi_errors_stream',
            'formatter' : 'default',
        },
        'syslog_local7' : {
            'class'     : 'logging.handlers.SysLogHandler',
            'formatter' : 'syslog',
            'address'   : '/dev/log',
            'facility'  : 'local7',
        },
    },
    'loggers' : {
        'root' : {
            'level'      : 'INFO',
            'handlers'   : ['wsgi'],
            'propagate'  : False,
        },
        'gunicorn.error' : {
            'level'      : 'INFO',
            'handlers'   : [os.getenv('GUNICORN_ERROR_LOG_HANDLER', 'syslog_local7')],
            'propagate'  : False,
        },
        'indi_allsky' : {
            'level'      : 'INFO',
            'handlers'   : [],  # indi_allsky handles it own logging
            'propagate'  : False,
        },
    }
})

logger = logging.getLogger('indi_allsky')

def set_winsize(fd, row, col):
    try:
        winsize = struct.pack("HHHH", int(row), int(col), 0, 0)
        fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)
        logger.info(f"PTY: Winsize set to {row}x{col}")
    except Exception as e:
        logger.error(f"PTY: set_winsize error: {e}")

def read_and_forward_pty_output():
    max_read_bytes = 1024 * 20
    logger.info("PTY: Starting output background task")
    while True:
        socketio.sleep(0.01)
        fd = terminal_state.get("fd")
        sid = terminal_state.get("active_sid")
        
        if fd and sid:
            try:
                (data_ready, _, _) = select.select([fd], [], [], 0)
                if data_ready:
                    output = os.read(fd, max_read_bytes).decode(errors="ignore")
                    socketio.emit("pty-output", {"output": output}, to=sid)
            except Exception as e:
                logger.error(f"PTY: Read error: {e}")
                terminal_state["fd"] = None
                terminal_state["child_pid"] = None
                terminal_state["background_task_started"] = False
                break
        elif not sid:
            socketio.sleep(0.5)
        else:
            terminal_state["background_task_started"] = False
            break

@socketio.on("connect")
def terminal_on_connect():
    sid = getattr(request, 'sid', 'unknown')
    # Use referrer to ensure we only fork shell for the actual shell page
    referrer = request.referrer or ""
    if "/system/shell" not in referrer:
        return

    logger.info(f"PTY: ULTIMATE CONNECT SID={sid}")
    terminal_state["active_sid"] = sid
    
    if terminal_state.get("child_pid"):
        try:
            os.kill(terminal_state["child_pid"], 0)
            logger.info(f"PTY: ULTIMATE REUSE PID {terminal_state['child_pid']}")
            if not terminal_state["background_task_started"]:
                terminal_state["background_task_started"] = True
                socketio.start_background_task(target=read_and_forward_pty_output)
            
            if terminal_state["fd"]:
                socketio.sleep(0.2)
                os.write(terminal_state["fd"], b"\n")
            return
        except OSError:
            terminal_state["child_pid"] = None
            terminal_state["fd"] = None

    try:
        logger.info("PTY: ULTIMATE FORK bash")
        (child_pid, fd) = pty.fork()
    except Exception as e:
        logger.error(f"PTY: ULTIMATE FORK FAILED: {e}")
        return

    if child_pid == 0:
        os.execvp("/bin/bash", ["bash"])
    else:
        terminal_state["fd"] = fd
        terminal_state["child_pid"] = child_pid
        terminal_state["background_task_started"] = True
        set_winsize(fd, 24, 80)
        socketio.start_background_task(target=read_and_forward_pty_output)
        logger.info(f"PTY: ULTIMATE FORKED PID {child_pid}")

@socketio.on("pty-input")
def terminal_on_input(data):
    fd = terminal_state.get("fd")
    if fd:
        try:
            os.write(fd, data["input"].encode())
        except OSError:
            pass

@socketio.on("resize")
def terminal_on_resize(data):
    fd = terminal_state.get("fd")
    if fd:
        set_winsize(fd, data["rows"], data["cols"])

@socketio.on("ping")
def terminal_on_ping():
    sid = getattr(request, 'sid', 'unknown')
    logger.info(f"PTY: ULTIMATE PING SID={sid}")
    socketio.emit("pong", to=sid)

@socketio.on("disconnect")
def terminal_on_disconnect():
    sid = getattr(request, 'sid', 'unknown')
    logger.info(f"PTY: ULTIMATE DISCONNECT SID={sid}")
    if terminal_state["active_sid"] == sid:
        terminal_state["active_sid"] = None


def _sqlite_pragma_on_connect(dbapi_con, con_record):
    dbapi_con.execute('PRAGMA journal_mode=WAL')
    dbapi_con.execute('PRAGMA synchronous=NORMAL')
    dbapi_con.execute('PRAGMA busy_timeout=20000')


def create_app():
    """Construct the core application."""
    app = Flask(
        __name__,
        instance_relative_config=False,
    )

    flask_config = os.environ.get('INDI_ALLSKY_FLASK_CONFIG', '/etc/indi-allsky/flask.json')
    app.config.from_file(flask_config, load=json.load)

    csrf.init_app(app)

    socketio.init_app(app, path='/indi-allsky/socket.io', async_mode='threading', engineio_logger=logging.getLogger('indi_allsky'))

    app.register_blueprint(bp_allsky)
    app.register_blueprint(bp_auth_allsky)
    app.register_blueprint(bp_syncapi_allsky)
    app.register_blueprint(bp_actionapi_allsky)

    csrf.exempt(bp_syncapi_allsky)
    csrf.exempt(bp_actionapi_allsky)

    db.init_app(app)
    migrate.init_app(app, db, directory=app.config['MIGRATION_FOLDER'])


    login_manager = LoginManager()
    login_manager.login_view = 'auth_indi_allsky.login_view'
    login_manager.init_app(app)

    from .models import IndiAllSkyDbUserTable


    @login_manager.user_loader
    def load_user(user_id):
        return IndiAllSkyDbUserTable.query.get(int(user_id))


    with app.app_context():
        from sqlalchemy import event

        if db.engine.dialect.name == 'sqlite':
            event.listen(db.engine, 'connect', _sqlite_pragma_on_connect)

        return app


@bp_allsky.app_template_filter()
def basename(p):
    return Path(p).name
