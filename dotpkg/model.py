from dataclasses import dataclass
from pathlib import Path

from dotpkg.constants import DOTPKG_MANIFEST_NAME
from dotpkg.manifest.dotpkg import DotpkgManifest
from dotpkg.utils.log import error

import json

@dataclass
class Dotpkg:
    path: Path
    manifest: DotpkgManifest

@dataclass
class DotpkgRef:
    path: Path

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def manifest_path(self) -> Path:
        return self.path / DOTPKG_MANIFEST_NAME

    def read(self) -> Dotpkg:
        if not self.manifest_path.exists():
            error(f"Missing dotpkg.json manifest for '{self.name}'!")

        with open(str(self.manifest_path), 'r') as f:
            manifest = DotpkgManifest.from_dict(json.load(f))
        
        return Dotpkg(path=self.path, manifest=manifest)

@dataclass
class DotpkgRefs:
    refs: list[DotpkgRef]
    is_batch: bool

    def __iter__(self):
        return iter(self.refs)
