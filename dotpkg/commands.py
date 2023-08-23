from pathlib import Path

from dotpkg.install import install, uninstall
from dotpkg.manifest import manifest_name, batch_skip_reason
from dotpkg.options import Options
from dotpkg.resolve import cwd_dotpkgs, Dotpkg
from dotpkg.utils.log import info, warn
from dotpkg.utils.prompt import confirm

import sys

def install_cmd(raw_dotpkg_paths: list[str], opts: Options):
    is_batch = False

    if raw_dotpkg_paths:
        dotpkgs = [Dotpkg(Path(p)) for p in raw_dotpkg_paths]
    else:
        found = cwd_dotpkgs()
        dotpkgs = found.dotpkgs
        is_batch = found.is_batch

    if is_batch and not confirm(f"Install dotpkgs {', '.join(pkg.name for pkg in dotpkgs)}?", opts):
        print('Cancelling')
        sys.exit(0)

    for pkg in dotpkgs:
        path = pkg.path
        manifest = pkg.read_manifest()

        name = manifest_name(path, manifest)
        description = manifest.get('description', '')

        if is_batch and (skip_reason := batch_skip_reason(manifest)):
            warn(f'Skipping {name} ({skip_reason})')
            continue

        info(f'Installing {name} ({description})...')
        install(path, manifest, opts)

def uninstall_cmd(raw_dotpkg_paths: list[str], opts: Options):
    is_batch = False

    if raw_dotpkg_paths:
        dotpkgs = [Dotpkg(Path(p)) for p in raw_dotpkg_paths]
    else:
        found = cwd_dotpkgs()
        dotpkgs = found.dotpkgs
        is_batch = found.is_batch

    if is_batch and not confirm(f"Uninstall dotpkgs {', '.join(pkg.name for pkg in dotpkgs)}?", opts):
        print('Cancelling')
        sys.exit(0)

    for pkg in dotpkgs:
        path = pkg.path
        manifest = pkg.read_manifest()

        name = manifest_name(path, manifest)

        if is_batch and (skip_reason := batch_skip_reason(manifest)):
            warn(f'Skipping {name} ({skip_reason})')
            continue

        info(f"Uninstalling {name} ({manifest.get('description', '')})...")
        uninstall(path, manifest, opts)

def sync_cmd(dotpkgs: list[str], opts: Options):
    uninstall_cmd(dotpkgs, opts)
    install_cmd(dotpkgs, opts)
