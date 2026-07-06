"""PanelAgent single-exe launcher.

This is the entry point baked into the PyInstaller-built ``panelagent.exe``.
It:

1. Resolves the bundled resources (static frontend, inventory data, channel
   mappings) relative to the executable — works whether running from a
   PyInstaller bundle (``sys._MEIPASS``) or from a source checkout.
2. Starts the uvicorn backend, serving both the API and the static frontend
   at http://127.0.0.1:<port>.
3. Opens the default browser once the server is ready.
4. Blocks until Ctrl+C / window close, then shuts down cleanly.

Any startup error is written to ~/.panelagent/launcher.log AND stderr, so
the failure cause is visible even when launched by double-click.

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
import traceback
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


def _setup_logging(data_root: Path) -> Path:
    """Add a file handler so startup errors are persisted to disk."""
    log_file = data_root / "launcher.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )
    logging.getLogger().addHandler(file_handler)
    logging.getLogger().setLevel(logging.INFO)
    return log_file


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


def _open_browser_when_ready(port: int) -> None:
    """Poll the health endpoint in a background thread; open browser on success.

    Runs off the main thread so a missing browser (CI / headless) can't block
    the server startup.
    """
    import urllib.request

    url = f"http://{HOST}:{port}/api/v1/health"
    deadline = time.monotonic() + 60.0
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    logger.info("Backend ready, opening browser at %s", url)
                    try:
                        webbrowser.open(f"http://{HOST}:{port}/")
                    except Exception as exc:
                        logger.warning("Could not open browser: %s", exc)
                    return
        except Exception:
            time.sleep(0.5)
    logger.warning("Backend did not become ready within 60s; not opening browser.")


def main() -> int:
    data_root = _user_data_root()
    log_file = _setup_logging(data_root)

    logger.info("=" * 60)
    logger.info("PanelAgent launcher starting")
    logger.info("data_root=%s", data_root)
    logger.info("log_file=%s", log_file)
    logger.info("=" * 60)

    try:
        return _run(data_root)
    except Exception:
        # Last-resort capture: write the full traceback to the log file AND
        # stderr, then sleep briefly so the console window doesn't blink
        # closed when launched by double-click.
        logger.exception("Launcher crashed with an unhandled exception")
        traceback.print_exc()
        sys.stderr.flush()
        print(
            "\nPanelAgent 启动失败。详见：\n  " + str(log_file),
            file=sys.stderr,
        )
        try:
            time.sleep(15)
        except Exception:
            pass
        return 1


def _run(data_root: Path) -> int:
    resource_root = _resource_root()
    logger.info("resource_root=%s", resource_root)

    # Static frontend lives under the bundle's frontend/out.
    static_dir = resource_root / "frontend" / "out"
    if static_dir.is_dir():
        logger.info("Static frontend found at %s", static_dir)
        os.environ["STATIC_FRONTEND_DIR"] = str(static_dir)
    else:
        logger.warning(
            "Static frontend NOT found at %s; backend will serve API only.",
            static_dir,
        )

    # Point backend at the per-user data dir so SQLite + uploads are writable.
    os.environ["PANELAGENT_DATA_DIR"] = str(data_root)
    # Pin CORS to the same origin (browser hits the backend directly).
    os.environ["BACKEND_CORS_ORIGINS"] = (
        f"http://{HOST}:{DEFAULT_PORT},http://localhost:{DEFAULT_PORT}"
    )

    port = _find_free_port(DEFAULT_PORT)
    logger.info("Using port %d", port)

    # Kick off browser-opening watcher in the background.
    threading.Thread(target=_open_browser_when_ready, args=(port,), daemon=True).start()

    # Import AFTER env is configured so Settings picks up the overrides.
    logger.info("Importing backend modules (slow on first run)...")
    import uvicorn

    logger.info("Starting uvicorn on http://%s:%d", HOST, port)
    # Run uvicorn on the MAIN thread — any startup error (e.g. missing
    # module, port-in-use, import failure) propagates here and is logged.
    uvicorn.run(
        app="backend.app.main:app",
        host=HOST,
        port=port,
        log_level="info",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
