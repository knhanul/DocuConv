# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

project_dir = Path(SPECPATH)

block_cipher = None

a = Analysis(
    [str(project_dir / "main.py")],
    pathex=[str(project_dir)],
    binaries=[],
    datas=[
        (str(project_dir / "qml"), "qml"),
        (str(project_dir / "assets"), "assets"),
        (str(project_dir / "appsettings.json"), "."),
    ],
    hiddenimports=[
        "pythoncom",
        "pywintypes",
        "win32com.client",
        "pypdfium2",
        "pypdfium2_raw",
        "PIL",
    ],
    hookspath=[str(project_dir / "hooks")],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="POSID_DocConv",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_dir / "assets" / "posid_logo.ico"),
)
