# NOTE: This file is auto-generated from schemas/installs.v2.schema.json via scripts/generate-models
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
    
    src_paths: list[str] = field(default_factory=lambda: [])
    '''The paths of the linked-to files.'''
    
    @staticmethod
    def from_dict(d: dict[str, Any]) -> InstallsEntry:
        return InstallsEntry(
            target_dir=d['targetDir'],
            src_paths=[v for v in (d.get('srcPaths') or [])],
            paths=[v for v in (d.get('paths') or [])],
        )
    
    def to_dict(self) -> dict[str, Any]:
        return {
            'targetDir': self.target_dir,
            'srcPaths': [(v) for v in (self.src_paths)],
            'paths': [(v) for v in (self.paths)],
        }
    

@dataclass
class InstallsV2Manifest:
    '''A manifest keeping track of the installed locations of dotpkgs'''
    
    installs: dict[str, InstallsEntry] = field(default_factory=lambda: {})
    '''The installed dotpkgs, keyed by the relative paths to the source directories (containing the dotpkg.json manifests).'''
    
    version: Literal[2] = field(default_factory=lambda: 2)
    '''The version of the install manifest.'''
    
    @staticmethod
    def from_dict(d: dict[str, Any]) -> InstallsV2Manifest:
        return InstallsV2Manifest(
            version=d.get('version') or 2,
            installs={k: InstallsEntry.from_dict(v) for k, v in (d.get('installs') or {}).items()},
        )
    
    def to_dict(self) -> dict[str, Any]:
        return {
            'version': self.version,
            'installs': {k: (v.to_dict()) for k, v in (self.installs).items()},
        }
    

