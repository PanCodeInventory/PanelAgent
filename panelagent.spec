# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the PanelAgent single-exe launcher.

Built artifacts:
  - One-file exe: dist/panelagent.exe
  - Bundled: backend + root-level domain modules, static data files,
    bundled inventory CSVs, and the pre-built static frontend (frontend/out).

The exe, on launch, writes mutable state (SQLite DB, uploaded inventories)
to ~/.panelagent instead of the read-only bundle. See launcher.py.
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

# NOTE: inventory CSVs are deliberately NOT bundled. They contain real
# antibody data and are gitignored; users upload their own via the UI on
# first launch. Uploaded files persist under ~/.panelagent/inventory/.

# Pre-built static frontend (produced by `next build` with output: export)
out_dir = PROJECT_ROOT / "frontend" / "out"
if out_dir.is_dir():
    datas.append((str(out_dir), str(Path("frontend") / "out")))

# --- Hidden imports (modules imported dynamically via importlib) ----------
# The backend loads endpoints, schemas and services via import_module() with
# string literals (see backend/app/api/v1/router.py and the endpoints). PyInstaller's
# static analysis cannot follow these, so we collect EVERY .py module under
# backend/app/ plus the root-level domain modules.
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
    # Data file dependencies pulled in by pandas/openpyxl at runtime.
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
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
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
    name="panelagent",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    runtime_tmpdir=None,
    console=True,  # keep console so users see startup logs / shutdown message
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon="scripts/panelagent.ico",  # add an icon file if available
)
