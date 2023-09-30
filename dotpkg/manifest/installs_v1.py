# NOTE: This file is auto-generated from schemas/installs.v1.schema.json via scripts/generate-models
# Please do not edit it manually and adjust/re-run the script instead!

from __future__ import annotations
from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Literal
from typing import Optional

@dataclass
class InstallsEntry:
    '''An installed dotpkg.'''
    
    target_dir: Optional[str] = None
    '''The installation path of the dotpkg.'''
    
    @staticmethod
    def from_dict(d: dict[str, Any]) -> InstallsEntry:
        return InstallsEntry(
            target_dir=d.get('targetDir') or None,
        )
    
    def to_dict(self) -> dict[str, Any]:
        return {
            'targetDir': self.target_dir,
        }
    

@dataclass
class InstallsV1Manifest:
    '''A manifest keeping track of the installed locations of dotpkgs'''
    
    installs: dict[str, InstallsEntry] = field(default_factory=lambda: {})
    '''The installed dotpkgs, keyed by the relative paths to the source directories (containing the dotpkg.json manifests).'''
    
    version: Literal[1] = field(default_factory=lambda: 1)
    '''The version of the install manifest.'''
    
    @staticmethod
    def from_dict(d: dict[str, Any]) -> InstallsV1Manifest:
        return InstallsV1Manifest(
            version=d.get('version') or 1,
            installs=d.get('installs') or {},
        )
    
    def to_dict(self) -> dict[str, Any]:
        return {
            'version': self.version,
            'installs': {k: v.to_dict() for k, v in self.installs.items()},
        }
    

