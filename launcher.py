"""PanelAgent single-exe launcher.

This is the entry point baked into the PyInstaller-built ``panelagent.exe``.
It:

1. Resolves the bundled resources (static frontend, inventory data, channel
   mappings) relative to the executable — works whether running from a
   PyInstaller bundle (``sys._MEIPASS``) or from a source checkout.
2. Starts the uvicorn backend in a background thread, serving both the API
   and the static frontend at http://127.0.0.1:<port>.
3. Opens the default browser once the server is ready.
4. Blocks until Ctrl+C / window close, then shuts down cleanly.

Run directly during development::

    PYTHONPATH=. STATIC_FRONTEND_DIR=frontend/out python launcher.py
"""

from __future__ import annotations

import logging
import os
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path

logger = logging.getLogger("panelagent.launcher")

DEFAULT_PORT = 8000
HOST = "127.0.0.1"


def _resource_root() -> Path:
    """Return the directory holding bundled resources.

    When frozen by PyInstaller, ``sys._MEIPASS`` is the temporary extraction
    directory. Otherwise fall back to this file's parent (the project root).
    """
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass)
    return Path(__file__).resolve().parent


def _user_data_root() -> Path:
    """Per-user writable directory for mutable state (SQLite DB, uploads).

    PyInstaller bundles are read-only, so the database and uploaded
    inventories must live outside the exe. We use a folder under the user's
    home directory and expose it via ``PANELAGENT_DATA_DIR`` so the backend
    (``admin_database.get_db_path`` and ``inventory_loader``) writes there.
    """
    base = Path.home() / ".panelagent"
    (base / "data").mkdir(parents=True, exist_ok=True)
    return base


def _find_free_port(preferred: int = DEFAULT_PORT) -> int:
    """Return ``preferred`` if free, otherwise the next free OS-assigned port.

    Uses SO_REUSEADDR so the subsequent uvicorn bind isn't blocked by the
    probe's TIME_WAIT.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((HOST, preferred))
            return preferred
        except OSError:
            pass
    # Fall back to an ephemeral port.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, 0))
        return s.getsockname()[1]


def _wait_for_server(port: int, timeout: float = 30.0) -> bool:
    """Poll the health endpoint until it responds or the timeout elapses."""
    import urllib.request

    deadline = time.monotonic() + timeout
    url = f"http://{HOST}:{port}/api/v1/health"
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.3)
    return False


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    resource_root = _resource_root()
    data_root = _user_data_root()

    # Static frontend lives under the bundle's frontend/out.
    static_dir = resource_root / "frontend" / "out"
    if not static_dir.is_dir():
        logger.warning(
            "Static frontend not found at %s; the backend will serve API only. "
            "Open http://%s:%d/api/v1/health to verify.",
            static_dir,
            HOST,
            DEFAULT_PORT,
        )

    # Point backend at the per-user data dir so SQLite + uploads are writable.
    os.environ.setdefault("PANELAGENT_DATA_DIR", str(data_root))
    # Serve the static frontend from the backend (single-port mode).
    if static_dir.is_dir():
        os.environ.setdefault("STATIC_FRONTEND_DIR", str(static_dir))
    # Pin CORS to the same origin (browser hits the backend directly).
    os.environ.setdefault(
        "BACKEND_CORS_ORIGINS",
        f"http://{HOST}:{DEFAULT_PORT},http://localhost:{DEFAULT_PORT}",
    )
    # Make project_root()-based data resolution land in the user data dir.
    os.chdir(data_root)

    port = _find_free_port(DEFAULT_PORT)
    if port != DEFAULT_PORT:
        logger.info("Port %d busy, using %d instead.", DEFAULT_PORT, port)

    # Import after env is configured so Settings picks up the overrides.
    logger.info("Importing backend modules (this is slow on first run)...")
    import uvicorn

    server = uvicorn.Server(
        uvicorn.Config(
            app="backend.app.main:app",
            host=HOST,
            port=port,
            log_level="warning",  # cut access-log noise; launcher logs readiness
            # Avoid signal handlers — we manage lifecycle ourselves.
        )
    )
    # Allow the server to install its own signal handlers off the main thread.
    server.install_signal_handlers = lambda: None

    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()

    logger.info("Waiting for backend to become ready...")
    if not _wait_for_server(port):
        logger.error("Backend failed to start within timeout. Exiting.")
        return 1

    url = f"http://{HOST}:{port}/"
    logger.info("PanelAgent is ready at %s", url)
    try:
        webbrowser.open(url)
    except Exception:
        pass  # headless / no default browser — not fatal

    print("\n" + "=" * 60)
    print(f"  PanelAgent 已启动：{url}")
    print("  关闭此窗口以停止服务。")
    print("=" * 60 + "\n")

    try:
        while server_thread.is_alive():
            server_thread.join(timeout=1.0)
    except KeyboardInterrupt:
        print("\n正在关闭...")
        server.should_exit = True
        server_thread.join(timeout=5.0)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
