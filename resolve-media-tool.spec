# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

block_cipher = None

# Collect data files for packages that need them
datas = []
datas += collect_data_files('basicsr')
datas += collect_data_files('realesrgan')
datas += collect_data_files('facexlib')
datas += collect_data_files('gfpgan')
datas += collect_data_files('torch')
datas += collect_data_files('torchvision')
datas += collect_data_files('cv2')

# Include app assets
datas += [('assets', 'assets')]

# Collect dynamic libs
binaries = []
binaries += collect_dynamic_libs('torch')
binaries += collect_dynamic_libs('cv2')

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=[
        'basicsr',
        'basicsr.archs',
        'basicsr.archs.rrdbnet_arch',
        'basicsr.data',
        'basicsr.data.degradations',
        'basicsr.utils',
        'basicsr.utils.download_util',
        'realesrgan',
        'realesrgan.archs',
        'realesrgan.utils',
        'facexlib',
        'facexlib.utils',
        'facexlib.detection',
        'facexlib.parsing',
        'gfpgan',
        'gfpgan.utils',
        'torch',
        'torchvision',
        'torchvision.transforms',
        'torchvision.transforms.functional',
        'cv2',
        'PIL',
        'numpy',
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtWidgets',
        'PyQt6.QtGui',
    ],
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
    [],
    exclude_binaries=True,
    name='resolve-media-tool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='assets/icon.png' if Path('assets/icon.png').exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='resolve-media-tool',
)
