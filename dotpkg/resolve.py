from dataclasses import dataclass
from pathlib import Path

from dotpkg.constants import DOTPKG_MANIFEST_NAME, IGNORED_NAMES
from dotpkg.manifest.dotpkg import DotpkgManifest
from dotpkg.options import Options
from dotpkg.utils.log import error

import json

# Dotpkg resolution

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

def cwd_dotpkgs(opts: Options) -> DotpkgRefs:
    cwd = opts.cwd.resolve()

    # Prefer current directory if it contains a manifest
    cwd_ref = DotpkgRef(cwd)
    if cwd_ref.manifest_path.exists():
        return DotpkgRefs(
            refs=[cwd_ref],
            is_batch=False,
        )
    
    # Otherwise resolve child directories
    return DotpkgRefs(
        refs=[
            ref
            for p in cwd.iterdir()
            for ref in [DotpkgRef(p)]
            if not p.name in IGNORED_NAMES and ref.manifest_path.exists()
        ],
        is_batch=True,
    )
