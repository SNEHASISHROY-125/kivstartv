# -*- mode: python ; coding: utf-8 -*-
import kivy, kivymd, sqlite3, requests, qrcode, fastapi, uvicorn 

# Import standard modules
import importlib.util
import os
import site

from PyInstaller.utils.hooks import collect_all

# Collect all necessary files for sqlite3
sqlite3_datas, sqlite3_binaries, sqlite3_hiddenimports = collect_all('sqlite3')
configparser_datas, configparser_binaries, configparser_hiddenimports = collect_all('configparser')


# Function to create runtime hook if needed
def create_runtime_hook():
    runtime_hook_path = os.path.abspath(os.path.join(os.getcwd(), "redirect_output.py"))
    if not os.path.exists(runtime_hook_path):
        with open(runtime_hook_path, 'w') as f:
            f.write('''
		# redirect_output.py - Runtime hook for PyInstaller
		import os
		import sys

		# Redirect stdout and stderr to log files in the application directory
		if hasattr(sys, '_MEIPASS'):
			log_dir = os.path.join(os.path.dirname(sys.executable), 'logs')
			if not os.path.exists(log_dir):
				try:
					os.makedirs(log_dir)
				except:
					pass
			try:
				sys.stdout = open(os.path.join(log_dir, 'stdout.log'), 'w')
				sys.stderr = open(os.path.join(log_dir, 'stderr.log'), 'w')
			except:
				pass
	''')
    return runtime_hook_path

runtime_hook_path = create_runtime_hook()

# Find and add package paths
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
        ('./kv', './kv'),
        ('./src', './src'),
        ('./sources', './sources'),
        ('./icon.png', './'),
		('./app.conf', './'),
		('./create_db.py', './'),
		('./manager.py', './'),
		('./remote_server.py', './'),
		('./update/main.py', './update/main.py'),
		('./redirect_output.py', './'),
		*sqlite3_datas,  # Add SQLite3 data files
        *configparser_datas,
        *extra_datas,
    ],
    hiddenimports=[
        'kivymd.tools.packaging.pyinstaller',  # Fixed: Using module name instead of path
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
        # Adding common Kivy modules that might be needed
        'kivy.core.window.window_sdl2',
        'kivy.core.text',
        'kivy.core.text.text_sdl2',
        'kivy.core.text.markup',
        'kivy.core.audio',
        'kivy.core.camera',
        'kivy.core.clipboard',
        'kivy.core.image',
        'kivy.core.spelling',
        'kivy.core.video',
        'kivy.core.video.video_ffmpeg',
        'kivy.graphics.tesselator',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[runtime_hook_path],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='kivstarTV',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Set to True temporarily for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    icon='./icon.png'
)

# Use COLLECT to gather all dependencies in a directory
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='kivstarTV',
)