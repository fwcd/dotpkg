from dataclasses import dataclass
from pathlib import Path

@dataclass
class Options:
    cwd: Path = Path.cwd()
    home: Path = Path.home()
    dry_run: bool = False
    assume_yes: bool = False
    safe_mode: bool = False
    update_install_manifest: bool = False
