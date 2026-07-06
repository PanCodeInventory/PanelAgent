# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the PanelAgent macOS app (Apple Silicon / arm64).

Built artifacts:
  - dist/PanelAgent.app (standard macOS application bundle)

Same bundling strategy as panelagent.spec (Windows), but produces a .app
via BUNDLE() with an Info.plist. Mutable state (SQLite DB, uploaded
inventories) is written to ~/.panelagent at runtime — see launcher.py.

Build (on an Apple Silicon Mac, or via the macOS CI job):
    python -m PyInstaller panelagent-mac.spec --noconfirm --clean
"""

from pathlib import Path

block_cipher = None

PROJECT_ROOT = Path(SPECPATH).resolve()

# --- Data files to bundle (read-only resources) ---------------------------
datas = []

# Static JSON data files referenced via project_root()
for json_file in [
    "channel_mapping.json",
    "fluorochrome_brightness.json",
    "spectral_data.json",
]:
    src = PROJECT_ROOT / json_file
    if src.is_file():
        datas.append((str(src), "."))

# NOTE: inventory CSVs are deliberately NOT bundled (same as Windows spec).

# Pre-built static frontend (produced by `next build` with output: export)
out_dir = PROJECT_ROOT / "frontend" / "out"
if out_dir.is_dir():
    datas.append((str(out_dir), str(Path("frontend") / "out")))

# --- Hidden imports (same set as the Windows spec) -----------------------
_backend_modules = []
_backend_root = PROJECT_ROOT / "backend" / "app"
if _backend_root.is_dir():
    for f in _backend_root.rglob("*.py"):
        if f.name == "__init__.py":
            continue
        rel = f.relative_to(PROJECT_ROOT).with_suffix("")
        _backend_modules.append(".".join(rel.parts))

hiddenimports = [
    "data_preprocessing",
    "panel_generator",
    "llm_api_client",
    "spectral_viewer",
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "backend.app.main",
    "openpyxl",
] + _backend_modules

a = Analysis(
    ["launcher.py"],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="PanelAgent",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # UPX is unreliable on macOS arm64
    console=True,  # macOS: run as a terminal app so users see startup output;
                   # logs also go to ~/.panelagent/launcher.log
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch="arm64",
)

# NOTE: A proper .app bundle (BUNDLE) is desirable for the dock-icon UX, but
# PyInstaller's BUNDLE step produced an empty directory in CI (the .app
# wasn't materialized). Falling back to a single-file Unix executable — same
# launcher, same UX as the Windows exe. The release zips this as
# PanelAgent-mac-arm64. Users run it from Terminal or via a wrapper.

