# -*- mode: python ; coding: utf-8 -*-
import sv_ttk

block_cipher = None



sv_ttk_folder = os.path.dirname(sv_ttk.__file__)

# Collect all the image files
added_files = [
    ('img/', 'img'),
    ('theme/', 'theme'),
    ('azure.tcl', '.'),
    (sv_ttk_folder, 'sv_ttk'),
]


a = Analysis(
    ['cubeControl.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[],
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
    name='cubeControl',
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
)
