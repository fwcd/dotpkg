# NOTE: This file is auto-generated from schemas/installs.v1.schema.json via scripts/generate-models
# Please do not edit it manually and adjust/re-run the script instead!

from __future__ import annotations
from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Literal
from typing import Optional

@dataclass
class InstallsV1Manifest:
    '''A manifest keeping track of the installed locations of dotpkgs'''
    
    @dataclass
    class InstallsEntry:
        '''An installed dotpkg.'''
        
        target_dir: Optional[str] = None
        '''The installation path of the dotpkg.'''
        
        @classmethod
        def from_dict(cls, d: dict[str, Any]):
            return cls(
                target_dir=d.get('targetDir') or None,
            )
        
        def to_dict(self) -> dict[str, Any]:
            return {
                'targetDir': self.target_dir,
            }
        
    
    installs: dict[str, InstallsV1Manifest.InstallsEntry] = field(default_factory=lambda: {})
    '''The installed dotpkgs, keyed by the relative paths to the source directories (containing the dotpkg.json manifests).'''
    
    version: Literal[1] = field(default_factory=lambda: 1)
    '''The version of the install manifest.'''
    
    @classmethod
    def from_dict(cls, d: dict[str, Any]):
        return cls(
            version=d.get('version') or 1,
            installs={k: InstallsV1Manifest.InstallsEntry.from_dict(v) for k, v in (d.get('installs') or {}).items()},
        )
    
    def to_dict(self) -> dict[str, Any]:
        return {
            'version': self.version,
            'installs': {k: (v.to_dict()) for k, v in (self.installs).items()},
        }
    

