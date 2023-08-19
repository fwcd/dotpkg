from dataclasses import dataclass

@dataclass
class Options:
    dry_run: bool
    assume_yes: bool
    safe_mode: bool
    relative_target_path: bool
    update_install_manifest: bool
