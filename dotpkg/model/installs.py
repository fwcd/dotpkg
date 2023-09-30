from dataclasses import dataclass

@dataclass
class Installs:
    '''A manifest keeping track of the installed locations of dotpkgs'''
    
    version: int
    '''The version of the install manifest.'''

