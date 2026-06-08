# Terminal Emulation Research Log

This document tracks the technical attempts and findings for the browser-based terminal emulation feature in `indi-allsky`.

## Status: Paused
**Conclusion:** The Socket.IO engine successfully receives data from the browser through Apache/Gunicorn, but the Python application handlers fail to fire within the Gunicorn worker environment despite consolidation.

---

## 1. Diagnostic Findings

### Infrastructure (Successful)
*   **Reverse Proxy**: Apache `ProxyPass` is correctly configured with `upgrade=websocket`. Logs confirm that binary Socket.IO packets (`ping`, `resize`, `pty-input`) reach the backend.
*   **Backend Path**: The correct path for Socket.IO is `/indi-allsky/socket.io`. Using `/socket.io` without the prefix causes routing failures in Apache.
*   **Transport**: WebSocket transport is the most stable path through the proxy. Polling transport (fallback) frequently results in `503 Service Unavailable` errors.

### The "Last Mile" Failure
Even with handlers consolidated into the application factory (`__init__.py`), the `flask-socketio` engine does not trigger the `@socketio.on` methods. 
*   **Symptom**: Gunicorn logs show `socket.receive()` for a packet, but no corresponding `PTY: ...` application log follows.
*   **Probable Cause**: The `socketio` object registry is likely being lost or isolated during the Gunicorn process fork (`gthread` worker class), resulting in the engine running in a "deaf" state.

---

## 2. Attempts & Configurations

### Attempt 1: Separate Module (`terminal.py`)
*   **Approach**: Handlers defined in a separate file, registered via a function called in `create_app`.
*   **Result**: Failed. Initial connection worked occasionally, but reloads were ignored.

### Attempt 2: Class-based Namespace (`/pty`)
*   **Approach**: Used `flask_socketio.Namespace` to encapsulate terminal state.
*   **Result**: Failed. The engine received packets tagged with the namespace, but the class methods were never called.

### Attempt 3: Shared Extension Pattern
*   **Approach**: Created `extensions.py` to hold the `socketio` instance, allowing top-level decorators in `terminal.py`.
*   **Result**: Failed. Solved circular imports but didn't fix the "deaf" handlers.

### Attempt 4: Simplified Default Namespace (`/`)
*   **Approach**: Removed the `/pty` prefix and moved to the default namespace to simplify routing.
*   **Result**: Partially worked for the first connection, but subsequent events (`ping`, `resize`) were ignored.

### Attempt 5: Path Alignment
*   **Discovery**: Found that Apache strips the `/indi-allsky` prefix.
*   **Correction**: Aligned the Socket.IO `path` setting to match what Gunicorn actually receives. Cleared console 404/503 errors.

### Attempt 6: "Ultimate" Consolidation
*   **Approach**: Moved all handlers, state, and PTY logic into `indi_allsky/flask/__init__.py` to eliminate every possible module/timing variable.
*   **Result**: Failed. Proved that even with zero dependencies, the engine and handlers are disconnected in the Gunicorn environment.

---

## 3. Future Recommendations

If this feature is revisited, the following paths are recommended:

1.  **Async Mode Swap**: Change Gunicorn from `gthread` to `eventlet` or `gevent`. This requires installing `eventlet` and performing monkey-patching (`eventlet.monkey_patch()`) at the very top of `app.py` and `wsgi.py`.
2.  **Standalone Terminal Service**: Run the terminal emulation as a separate process (e.g., a small Node.js or Python app on a different port) and proxy to it via Apache. This avoids the Flask/Gunicorn worker lifecycle issues entirely.
3.  **Engineio Debugging**: Enable `engineio_logger=True` and `logger=True` in the `SocketIO` constructor to get verbose hex-dumps of the low-level handshake.
