from dataclasses import dataclass

@dataclass
class Scripts:
    '''Scripts for handling lifecycle events.'''
    preinstall: str
    install: str
    postinstall: str
    preuninstall: str
    uninstall: str
    postuninstall: str

@dataclass
class Dotpkg:
    '''A configuration file for describing dotfile packages (dotpkg.json)'''
    name: str
    description: str
    requires_on_path: str
    platforms: str
    host_specific_files: str
    ignored_files: str
    renames: dict[str, str]
    target_dir: str
    create_target_dir_if_needed: bool
    touch_files: str
    skip_during_batch_install: bool
    copy: bool
    is_scripts_only: bool
    requires: str
    scripts: Scripts

