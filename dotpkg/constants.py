from pathlib import Path

DOTPKG_MANIFEST_NAME = 'dotpkg.json'
INSTALL_MANIFEST_DIR = Path('.').resolve()
INSTALL_MANIFEST_NAME = 'installs.json'
INSTALL_MANIFEST_PATH = INSTALL_MANIFEST_DIR / INSTALL_MANIFEST_NAME
INSTALL_MANIFEST_VERSION = 2
IGNORED_NAMES = {DOTPKG_MANIFEST_NAME, INSTALL_MANIFEST_NAME, '.git', '.gitignore', '.DS_Store'}