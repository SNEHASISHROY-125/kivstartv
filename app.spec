# -*- mode: python ; coding: utf-8 -*-
import kivy , kivymd , sqlite3, datetime, PyPDF2
from kivy_deps import sdl2, glew
from kivymd import hooks_path as kivymd_hooks_path


a = Analysis(
    ['./app/app.py'],
    pathex=[],
    binaries=[],
    datas=[('./assets/icon-256.ico', './assets'), ('./assets/icon-512.png', './assets') , ('./assets/pdf.png', './assets'), ('./assets/gif.gif', './assets') , ('./assets/404-error.png', './assets'), ('./assets/no-results-found.png', './assets') , ('./assets/3d-glassy-purple-cross-in-circle.png', './assets')],
    hiddenimports=[kivymd_hooks_path],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
    name='TrackMyPC_V1.7.1',
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
    icon='./assets/icon-256.ico'
)
