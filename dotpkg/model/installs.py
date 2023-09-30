from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass
class Installs:
    '''A manifest keeping track of the installed locations of dotpkgs'''
    
    version: int
    '''The version of the install manifest.'''
    
    @staticmethod
    def from_dict(d: dict[str, Any]) -> Installs:
        return Installs(
            version=d['version'],
        )
    
    def to_dict(self) -> dict[str, Any]:
        return {
            'version': self.version,
        }
    

