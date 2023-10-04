from dataclasses import dataclass
from pathlib import Path

@dataclass
class Options:
    cwd: Path = Path.cwd()
    home: Path = Path.home()
    safe_mode: bool = False
    update_install_manifest: bool = True

    dry_run: bool = False # TODO: Replace with a 'file system' interface
    assume_yes: bool = False # TODO: Replace with a 'decider' interface

    @property
    def state_dir(self) -> Path:
        return self.home / '.local' / 'state' / 'dotpkg'
