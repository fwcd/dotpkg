# NOTE: This file is auto-generated from schemas/installs.v3.schema.json via scripts/generate-models
# Please do not edit it manually and adjust/re-run the script instead!

from __future__ import annotations
from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Literal

@dataclass
class InstallsEntry:
    '''An installed dotpkg.'''
    
    target_dir: str
    '''The installation path of the dotpkg.'''
    
    paths: list[str] = field(default_factory=lambda: [])
    '''The paths to the installed links.'''
    
    sha256sums: list[str] = field(default_factory=lambda: [])
    '''The SHA256 checksums of the installed files. Mainly relevant for copy packages.'''
    
    src_paths: list[str] = field(default_factory=lambda: [])
    '''The paths of the linked-to/copied files.'''
    
    @staticmethod
    def from_dict(d: dict[str, Any]) -> InstallsEntry:
        return InstallsEntry(
            target_dir=d['targetDir'],
            src_paths=[v for v in (d.get('srcPaths') or [])],
            paths=[v for v in (d.get('paths') or [])],
            sha256sums=[v for v in (d.get('sha256sums') or [])],
        )
    
    def to_dict(self) -> dict[str, Any]:
        return {
            'targetDir': self.target_dir,
            'srcPaths': [(v) for v in (self.src_paths)],
            'paths': [(v) for v in (self.paths)],
            'sha256sums': [(v) for v in (self.sha256sums)],
        }
    

@dataclass
class InstallsV3Manifest:
    '''A manifest keeping track of the installed locations of dotpkgs'''
    
    installs: dict[str, InstallsEntry] = field(default_factory=lambda: {})
    '''The installed dotpkgs, keyed by the relative paths to the source directories (containing the dotpkg.json manifests).'''
    
    version: Literal[3] = field(default_factory=lambda: 3)
    '''The version of the install manifest.'''
    
    @staticmethod
    def from_dict(d: dict[str, Any]) -> InstallsV3Manifest:
        return InstallsV3Manifest(
            version=d.get('version') or 3,
            installs={k: InstallsEntry.from_dict(v) for k, v in (d.get('installs') or {}).items()},
        )
    
    def to_dict(self) -> dict[str, Any]:
        return {
            'version': self.version,
            'installs': {k: (v.to_dict()) for k, v in (self.installs).items()},
        }
    

