from dataclasses import dataclass

@dataclass
class Options:
    dry_run: bool = False
    assume_yes: bool = False
    safe_mode: bool = False
    update_install_manifest: bool = False
