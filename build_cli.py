#!/usr/bin/env python3
import PyInstaller.__main__
import os
import shutil
from pathlib import Path

def build_cli():
    # Clean previous builds
    for dir_name in ['build', 'dist']:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
    
    # Create the spec file with optimized settings
    spec_content = '''
# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['client/cli.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'rich.markup',
        'rich.live',
        'rich.panel',
        'rich.progress',
        'rich.style',
        'rich.console',
        'typer.completion',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

# Remove unnecessary modules to reduce size
excluded_modules = {
    'tkinter', 'PyQt5', 'PySide2', 'wx', 'matplotlib',
    'notebook', 'scipy', 'pandas', 'PIL', 'pygame'
}

def exclude_module(module_name):
    for item in a.pure:
        if item[0].startswith(module_name):
            a.pure.remove(item)
            
for module in excluded_modules:
    exclude_module(module)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='command-cli',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''
    
    # Write the spec file
    with open('command-cli.spec', 'w') as f:
        f.write(spec_content.lstrip())
    
    print("Building CLI executable...")
    PyInstaller.__main__.run([
        'command-cli.spec',
        '--clean',
        '--onefile',
        '--name=command-cli',
    ])
    
    # Clean up build artifacts
    if os.path.exists('build'):
        shutil.rmtree('build')
    if os.path.exists('command-cli.spec'):
        os.remove('command-cli.spec')
    
    # Make the executable executable
    executable_path = Path('dist/command-cli')
    if executable_path.exists():
        executable_path.chmod(0o755)
        print(f"\nBuild successful! Executable created at: {executable_path}")
        print("\nYou can run it with:")
        print(f"./dist/command-cli --help")
    else:
        print("\nBuild failed!")

if __name__ == '__main__':
    build_cli() 