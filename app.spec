# -*- mode: python ; coding: utf-8 -*-
import kivy , kivymd , sqlite3 , requests , qrcode , fastapi ,uvicorn
from kivy_deps import sdl2, glew
from kivymd import hooks_path as kivymd_hooks_path

# Guide's : Pyinstaller [for .exe] & InnoSetup [for installer]
# https://www.youtube.com/watch?v=p3tSLatmGvU

# Add importlib-metadata for python-multipart if needed
import importlib.util
import os
import site

# Add this near the top, after imports
runtime_hook_path = os.path.abspath(os.path.join(os.getcwd(), "redirect_output.py"))

# Find and add python_multipart, multipart, and ffpyplayer package folders
def get_package_path(pkg_name):
    spec = importlib.util.find_spec(pkg_name)
    if spec and spec.submodule_search_locations:
        return spec.submodule_search_locations[0]
    return None

multipart_path = get_package_path("multipart")
python_multipart_path = get_package_path("python_multipart")
ffpyplayer_path = get_package_path("ffpyplayer")

extra_datas = []
if multipart_path:
    extra_datas.append((multipart_path, "multipart"))
if python_multipart_path:
    extra_datas.append((python_multipart_path, "python_multipart"))
if ffpyplayer_path:
    extra_datas.append((ffpyplayer_path, "ffpyplayer"))

a = Analysis(
    ['./main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('./archive', './archive'),
        ('./src', './src'),
        ('./sources', './sources'),
        ('./icon.png', './'),
        ('./', './'),
        *extra_datas,
    ],
    hiddenimports=[
        kivymd_hooks_path, 
        'ffmpeg',
        'ffpyplayer',
        'ffpyplayer.player',
        'ffpyplayer.pic',
        'ffpyplayer.tools',
        'fastapi', 
        'starlette', 
        'pydantic', 
        'fastapi.middleware.cors',
        'fastapi.staticfiles',
        'uvicorn',
        'requests',
        'qrcode',
        'multipart', 
        'python_multipart',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[runtime_hook_path],  # <-- Add this line
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
    name='kivstarTV_V1.7.1',
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
    icon='./icon.ico'
)
