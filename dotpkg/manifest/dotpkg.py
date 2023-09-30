# NOTE: This file is auto-generated from schemas/dotpkg.schema.json via scripts/generate-models
# Please do not edit it manually and adjust/re-run the script instead!

from __future__ import annotations
from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Literal
from typing import Optional

@dataclass
class Scripts:
    '''Scripts for handling lifecycle events.'''
    
    install: Optional[str] = None
    '''A shell command to invoke during installation.'''
    
    postinstall: Optional[str] = None
    '''A shell command to invoke after installation.'''
    
    postuninstall: Optional[str] = None
    '''A shell command to invoke after uninstallation.'''
    
    preinstall: Optional[str] = None
    '''A shell command to invoke prior to installation.'''
    
    preuninstall: Optional[str] = None
    '''A shell command to invoke prior to uninstallation.'''
    
    uninstall: Optional[str] = None
    '''A shell command to invoke during uninstallation.'''
    
    @staticmethod
    def from_dict(d: dict[str, Any]) -> Scripts:
        return Scripts(
            preinstall=d.get('preinstall') or None,
            install=d.get('install') or None,
            postinstall=d.get('postinstall') or None,
            preuninstall=d.get('preuninstall') or None,
            uninstall=d.get('uninstall') or None,
            postuninstall=d.get('postuninstall') or None,
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
class DotpkgManifest:
    '''A configuration file for describing dotfile packages (dotpkg.json)'''
    
    name: str
    '''The name of the dotpkg (usually a short, kebab-cases identifier e.g. referring to the program configured). By default this is the name of the parent dir.'''
    
    copy: bool = field(default_factory=lambda: False)
    '''Whether to copy the files instead of linking them.'''
    
    create_target_dir_if_needed: bool = field(default_factory=lambda: False)
    '''Creates the first directory from the 'targetDir' list if none exists.'''
    
    description: str = field(default_factory=lambda: '')
    '''A long, human-readable description of what this dotpkg contains (e.g. 'configurations for xyz').'''
    
    host_specific_files: list[str] = field(default_factory=lambda: [])
    '''A list of file (glob) patterns that are considered to be host-specific. Files that are irrelevant to the current host (e.g. those for other hosts) will be ignored. Each pattern should include '${hostname}' to refer to such files.'''
    
    ignored_files: list[str] = field(default_factory=lambda: [])
    '''A list of file (glob) patterns that are to be ignored, i.e. not linked. This could e.g. be useful to store generic scripts in the dotpkg that are not intended to be linked into some config directory.'''
    
    is_scripts_only: bool = field(default_factory=lambda: False)
    '''Implicitly ignores all files for linking. Useful for packages that only use their install/uninstall scripts.'''
    
    platforms: list[str] = field(default_factory=lambda: [])
    '''The platforms that this dotpkg is intended for. An empty array (the default) means support for all platforms. Only relevant if 'dotpkg install' is invoked without arguments.'''
    
    renames: dict[str, str] = field(default_factory=lambda: {})
    '''A set of rename rules that are applied to the symlink names. If empty or left unspecified, the file names are the same as their originals.'''
    
    requires: Optional[Literal['logout', 'reboot']] = None
    '''Whether (un)installation requires logging out or a reboot of the computer.'''
    
    requires_on_path: list[str] = field(default_factory=lambda: [])
    '''Binaries requires on the PATH for the package to be automatically installed when invoking 'dotpkg install' (usually the program configured, e.g. 'code'). Only relevant if 'dotpkg install' is invoked without arguments, otherwise the package will always be installed.'''
    
    scripts: Scripts = field(default_factory=lambda: Scripts())
    '''Scripts for handling lifecycle events.'''
    
    skip_during_batch_install: bool = field(default_factory=lambda: False)
    '''Whether to skip the package during batch-install.'''
    
    target_dir: list[str] = field(default_factory=lambda: ['${home}'])
    '''The target directory that the files from the dotpkg should be linked into. The first existing path from this list will be chosen (this is useful for cross-platform dotpkgs, since some programs place their configs in an OS-specific location).'''
    
    touch_files: list[str] = field(default_factory=lambda: [])
    '''A list of paths to create in the target directory, if not already existing. Useful e.g. for private/ignored configs that are included by a packaged config.'''
    
    @staticmethod
    def from_dict(d: dict[str, Any]) -> DotpkgManifest:
        return DotpkgManifest(
            name=d['name'],
            description=d.get('description') or '',
            requires_on_path=d.get('requiresOnPath') or [],
            platforms=d.get('platforms') or [],
            host_specific_files=d.get('hostSpecificFiles') or [],
            ignored_files=d.get('ignoredFiles') or [],
            renames=d.get('renames') or {},
            target_dir=d.get('targetDir') or ['${home}'],
            create_target_dir_if_needed=d.get('createTargetDirIfNeeded') or False,
            touch_files=d.get('touchFiles') or [],
            skip_during_batch_install=d.get('skipDuringBatchInstall') or False,
            copy=d.get('copy') or False,
            is_scripts_only=d.get('isScriptsOnly') or False,
            requires=d.get('requires') or None,
            scripts=Scripts.from_dict(d.get('scripts') or {}),
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
            'scripts': self.scripts.to_dict(),
        }
    

