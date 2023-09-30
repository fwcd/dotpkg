from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass
class Installs:
    '''An installed dotpkg.'''
    
    target_dir: str
    '''The installation path of the dotpkg.'''
    
    @staticmethod
    def from_dict(d: dict[str, Any]) -> Installs:
        return Installs(
            target_dir=d['targetDir'],
        )
    
    def to_dict(self) -> dict[str, Any]:
        return {
            'targetDir': self.target_dir,
        }
    

@dataclass
class InstallsV1Manifest:
    '''A manifest keeping track of the installed locations of dotpkgs'''
    
    installs: dict[str, Installs]
    '''The installed dotpkgs, keyed by the relative paths to the source directories (containing the dotpkg.json manifests).'''
    
    version: int
    '''The version of the install manifest.'''
    
    @staticmethod
    def from_dict(d: dict[str, Any]) -> InstallsV1Manifest:
        return InstallsV1Manifest(
            version=d['version'],
            installs=d['installs'],
        )
    
    def to_dict(self) -> dict[str, Any]:
        return {
            'version': self.version,
            'installs': self.installs,
        }
    

