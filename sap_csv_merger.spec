# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all

block_cipher = None

certifi_datas, certifi_binaries, certifi_hiddenimports = collect_all('certifi')

a = Analysis(
    ['sap_merge.py'],
    pathex=[],
    binaries=certifi_binaries,
    datas=[('theme.py', '.'), ('fujifilm_bg.png', '.')] + certifi_datas,
    hiddenimports=['tkinter', 'csv', 'pathlib', 'datetime', 'os', 'shutil'] + certifi_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='SAP_CSV_Merger',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI app, no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)
