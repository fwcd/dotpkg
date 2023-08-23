from dataclasses import dataclass

@dataclass
class Options:
    dry_run: bool
    assume_yes: bool
    safe_mode: bool
    update_install_manifest: bool
