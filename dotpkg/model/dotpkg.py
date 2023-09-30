from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass
class Scripts:
    '''Scripts for handling lifecycle events.'''
    
    preinstall: str
    '''A shell command to invoke prior to installation.'''
    
    install: str
    '''A shell command to invoke during installation.'''
    
    postinstall: str
    '''A shell command to invoke after installation.'''
    
    preuninstall: str
    '''A shell command to invoke prior to uninstallation.'''
    
    uninstall: str
    '''A shell command to invoke during uninstallation.'''
    
    postuninstall: str
    '''A shell command to invoke after uninstallation.'''
    
    @staticmethod
    def from_dict(d: dict[str, Any]) -> Scripts:
        return Scripts(
            preinstall=d['preinstall'],
            install=d['install'],
            postinstall=d['postinstall'],
            preuninstall=d['preuninstall'],
            uninstall=d['uninstall'],
            postuninstall=d['postuninstall'],
        )
    
    def to_dict(self) -> dict[str, Any]:
        return {
            'preinstall': self.preinstall,
            'install': self.install,
            'postinstall': self.postinstall,
            'preuninstall': self.preuninstall,
            'uninstall': self.uninstall,
            'postuninstall': self.postuninstall,
        }
    

@dataclass
class Dotpkg:
    '''A configuration file for describing dotfile packages (dotpkg.json)'''
    
    name: str
    '''The name of the dotpkg (usually a short, kebab-cases identifier e.g. referring to the program configured). By default this is the name of the parent dir.'''
    
    description: str
    '''A long, human-readable description of what this dotpkg contains (e.g. 'configurations for xyz').'''
    
    requires_on_path: str
    '''Binaries requires on the PATH for the package to be automatically installed when invoking 'dotpkg install' (usually the program configured, e.g. 'code'). Only relevant if 'dotpkg install' is invoked without arguments, otherwise the package will always be installed.'''
    
    platforms: str
    '''The platforms that this dotpkg is intended for. An empty array (the default) means support for all platforms. Only relevant if 'dotpkg install' is invoked without arguments.'''
    
    host_specific_files: str
    '''A list of file (glob) patterns that are considered to be host-specific. Files that are irrelevant to the current host (e.g. those for other hosts) will be ignored. Each pattern should include '${hostname}' to refer to such files.'''
    
    ignored_files: str
    '''A list of file (glob) patterns that are to be ignored, i.e. not linked. This could e.g. be useful to store generic scripts in the dotpkg that are not intended to be linked into some config directory.'''
    
    renames: dict[str, str]
    '''A set of rename rules that are applied to the symlink names. If empty or left unspecified, the file names are the same as their originals.'''
    
    target_dir: str
    '''The target directory that the files from the dotpkg should be linked into. The first existing path from this list will be chosen (this is useful for cross-platform dotpkgs, since some programs place their configs in an OS-specific location).'''
    
    create_target_dir_if_needed: bool
    '''Creates the first directory from the 'targetDir' list if none exists.'''
    
    touch_files: str
    '''A list of paths to create in the target directory, if not already existing. Useful e.g. for private/ignored configs that are included by a packaged config.'''
    
    skip_during_batch_install: bool
    '''Whether to skip the package during batch-install.'''
    
    copy: bool
    '''Whether to copy the files instead of linking them.'''
    
    is_scripts_only: bool
    '''Implicitly ignores all files for linking. Useful for packages that only use their install/uninstall scripts.'''
    
    requires: str
    '''Whether (un)installation requires logging out or a reboot of the computer.'''
    
    scripts: Scripts
    '''Scripts for handling lifecycle events.'''
    
    @staticmethod
    def from_dict(d: dict[str, Any]) -> Dotpkg:
        return Dotpkg(
            name=d['name'],
            description=d['description'],
            requires_on_path=d['requiresOnPath'],
            platforms=d['platforms'],
            host_specific_files=d['hostSpecificFiles'],
            ignored_files=d['ignoredFiles'],
            renames=d['renames'],
            target_dir=d['targetDir'],
            create_target_dir_if_needed=d['createTargetDirIfNeeded'],
            touch_files=d['touchFiles'],
            skip_during_batch_install=d['skipDuringBatchInstall'],
            copy=d['copy'],
            is_scripts_only=d['isScriptsOnly'],
            requires=d['requires'],
            scripts=d['scripts'],
        )
    
    def to_dict(self) -> dict[str, Any]:
        return {
            'name': self.name,
            'description': self.description,
            'requiresOnPath': self.requires_on_path,
            'platforms': self.platforms,
            'hostSpecificFiles': self.host_specific_files,
            'ignoredFiles': self.ignored_files,
            'renames': self.renames,
            'targetDir': self.target_dir,
            'createTargetDirIfNeeded': self.create_target_dir_if_needed,
            'touchFiles': self.touch_files,
            'skipDuringBatchInstall': self.skip_during_batch_install,
            'copy': self.copy,
            'isScriptsOnly': self.is_scripts_only,
            'requires': self.requires,
            'scripts': self.scripts,
        }
    

