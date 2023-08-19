from pathlib import Path
from typing import Iterable, Any

from dotpkg.constants import DOTPKG_MANIFEST_NAME, IGNORED_NAMES
from dotpkg.utils.log import error

import json

# Dotpkg resolution

def cwd_dotpkgs() -> list[str]:
    return [
        p.name
        for p in Path.cwd().iterdir()
        if not p.name in IGNORED_NAMES and (p / DOTPKG_MANIFEST_NAME).exists()
    ]

def resolve_dotpkgs(dotpkgs: list[str]) -> Iterable[tuple[Path, dict[str, Any]]]:
    for dotpkg in dotpkgs:
        path = Path.cwd() / dotpkg
        manifest_path = path / DOTPKG_MANIFEST_NAME

        if not path.exists() or not path.is_dir():
            error(f"Dotpkg '{dotpkg}' does not exist in cwd!")
        if not manifest_path.exists():
            error(f"Missing dotpkg.json for '{dotpkg}'!")

        with open(str(manifest_path), 'r') as f:
            manifest = json.loads(f.read())

        yield path, manifest
