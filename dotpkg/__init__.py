import argparse
import json
import sys
import platform

from pathlib import Path
from typing import Iterable, Optional, Any

from dotpkg.constants import IGNORED_NAMES, DOTPKG_MANIFEST_NAME, INSTALL_MANIFEST_NAME
from dotpkg.install import install, uninstall
from dotpkg.manifest import manifest_name, unsatisfied_path_requirements
from dotpkg.options import Options
from dotpkg.utils.log import info, warn, error
from dotpkg.utils.prompt import confirm

if sys.version_info < (3, 9):
    print('Python version >= 3.9 is required!')
    sys.exit(1)

# Dotpkg resolution

def cwd_dotpkgs() -> list[str]:
    return [
        p.name
        for p in Path.cwd().iterdir()
        if not p.name in IGNORED_NAMES and (p / DOTPKG_MANIFEST_NAME).exists()
    ]

def resolve_dotpkgs(dotpkgs: list[str]) -> Iterable[tuple[Path, dict[str, Any]]]:
    for dotpkg in dotpkgs:
        path = Path.cwd() / dotpkg
        manifest_path = path / DOTPKG_MANIFEST_NAME

        if not path.exists() or not path.is_dir():
            error(f"Dotpkg '{dotpkg}' does not exist in cwd!")
        if not manifest_path.exists():
            error(f"Missing dotpkg.json for '{dotpkg}'!")

        with open(str(manifest_path), 'r') as f:
            manifest = json.loads(f.read())

        yield path, manifest

def batch_skip_reason(manifest: dict[str, Any]) -> Optional[str]:
    unsatisfied_reqs = list(unsatisfied_path_requirements(manifest))
    supported_platforms: set[str] = set(manifest.get('platforms', []))
    our_platform = platform.system().lower()
    skip_during_batch = manifest.get('skipDuringBatchInstall', False)

    if skip_during_batch:
        return f'Batch-install'
    if supported_platforms and (our_platform not in supported_platforms):
        return f"Platform {our_platform} is not supported, supported are {', '.join(sorted(supported_platforms))}"
    if unsatisfied_reqs:
        return f"Could not find {', '.join(unsatisfied_reqs)} on PATH"

    return None

# CLI

def install_cmd(dotpkgs: list[str], opts: Options):
    is_batch = False

    if not dotpkgs:
        dotpkgs = cwd_dotpkgs()
        is_batch = True
        if not confirm(f"Install dotpkgs {', '.join(dotpkgs)}?", opts):
            print('Cancelling')
            sys.exit(0)

    for path, manifest in resolve_dotpkgs(dotpkgs):
        name = manifest_name(path, manifest)
        description = manifest.get('description', '')

        if is_batch and (skip_reason := batch_skip_reason(manifest)):
            warn(f'Skipping {name} ({skip_reason})')
            continue

        info(f'Installing {name} ({description})...')
        install(path, manifest, opts)

def uninstall_cmd(dotpkgs: list[str], opts: Options):
    is_batch = False

    if not dotpkgs:
        dotpkgs = cwd_dotpkgs()
        is_batch = True
        if not confirm(f"Uninstall dotpkgs {', '.join(dotpkgs)}?", opts):
            print('Cancelling')
            sys.exit(0)

    for path, manifest in resolve_dotpkgs(dotpkgs):
        name = manifest_name(path, manifest)

        if is_batch and (skip_reason := batch_skip_reason(manifest)):
            warn(f'Skipping {name} ({skip_reason})')
            continue

        info(f"Uninstalling {name} ({manifest.get('description', '')})...")
        uninstall(path, manifest, opts)

def sync_cmd(dotpkgs: list[str], opts: Options):
    uninstall_cmd(dotpkgs, opts)
    install_cmd(dotpkgs, opts)

COMMANDS = {
    'install': install_cmd,
    'uninstall': uninstall_cmd,
    'sync': sync_cmd,
}

def main():
    parser = argparse.ArgumentParser(description='Dotfile package manager')
    parser.add_argument('-d', '--dry-run', action='store_true', help='Simulate a run without any modifications to the file system.')
    parser.add_argument('-y', '--assume-yes', action='store_true', help='Accept prompts with yes and run non-interactively (great for scripts)')
    parser.add_argument('-s', '--safe-mode', action='store_true', help='Skip any user-defined shell commands such as scripts.')
    parser.add_argument('--no-install-manifest', action='store_false', dest='update_install_manifest', help=f'Skips creating an install manifest ({INSTALL_MANIFEST_NAME}).')
    parser.add_argument('--relative-target-path', action='store_true', help='Install a relative path to the target dir into the install manifest.')
    parser.add_argument('command', choices=sorted(COMMANDS.keys()), help='The command to invoke')
    parser.add_argument('dotpkgs', nargs=argparse.ZERO_OR_MORE, help='The dotpkgs to install (all by default)')

    args = parser.parse_args()
    opts = Options(
        dry_run=args.dry_run,
        assume_yes=args.assume_yes,
        relative_target_path=args.relative_target_path,
        update_install_manifest=args.update_install_manifest,
        safe_mode=args.safe_mode,
    )

    if opts.dry_run:
        warn("Performing dry run (i.e. not actually changing any files)")

    COMMANDS[args.command](args.dotpkgs, opts)
