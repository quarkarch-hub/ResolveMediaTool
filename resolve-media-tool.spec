# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules

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

# Force-include package directories that are scanned at runtime
import site as _site
_sp = Path('.venv/lib/python3.12/site-packages')
datas += [(str(_sp / 'basicsr'), 'basicsr')]
datas += [(str(_sp / 'realesrgan'), 'realesrgan')]
datas += [(str(_sp / 'facexlib'), 'facexlib')]
datas += [(str(_sp / 'gfpgan'), 'gfpgan')]

# Collect dynamic libs
binaries = []
binaries += collect_dynamic_libs('torch')
binaries += collect_dynamic_libs('cv2')
binaries += collect_dynamic_libs('nvidia.cublas')
binaries += collect_dynamic_libs('nvidia.cuda_cupti')
binaries += collect_dynamic_libs('nvidia.cuda_nvrtc')
binaries += collect_dynamic_libs('nvidia.cuda_runtime')
binaries += collect_dynamic_libs('nvidia.cudnn')
binaries += collect_dynamic_libs('nvidia.cufft')
binaries += collect_dynamic_libs('nvidia.curand')
binaries += collect_dynamic_libs('nvidia.cusolver')
binaries += collect_dynamic_libs('nvidia.cusparse')
binaries += collect_dynamic_libs('nvidia.nccl')
binaries += collect_dynamic_libs('nvidia.nvjitlink')
binaries += collect_dynamic_libs('nvidia.nvtx')

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=[
        *collect_submodules('basicsr'),
        *collect_submodules('realesrgan'),
        *collect_submodules('facexlib'),
        *collect_submodules('gfpgan'),
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
