from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotpkg.constants import DOTPKG_MANIFEST_NAME, IGNORED_NAMES
from dotpkg.options import Options
from dotpkg.utils.log import error

import json

# Dotpkg resolution

@dataclass
class Dotpkg:
    path: Path

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def manifest_path(self) -> Path:
        return self.path / DOTPKG_MANIFEST_NAME

    def read_manifest(self) -> dict[str, Any]:
        if not self.manifest_path.exists():
            error(f"Missing dotpkg.json for '{self.name}'!")

        with open(str(self.manifest_path), 'r') as f:
            return json.loads(f.read())

@dataclass
class FoundDotpkgs:
    dotpkgs: list[Dotpkg]
    is_batch: bool

def cwd_dotpkgs(opts: Options) -> FoundDotpkgs:
    cwd = opts.cwd.resolve()

    # Prefer current directory if it contains a manifest
    if (cwd / DOTPKG_MANIFEST_NAME).exists():
        return FoundDotpkgs(
            dotpkgs=[Dotpkg(cwd)],
            is_batch=False,
        )
    
    # Otherwise resolve child directories
    return FoundDotpkgs(
        dotpkgs=[
            Dotpkg(p)
            for p in cwd.iterdir()
            if not p.name in IGNORED_NAMES and (p / DOTPKG_MANIFEST_NAME).exists()
        ],
        is_batch=True,
    )
