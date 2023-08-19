from dotpkg.install import install, uninstall
from dotpkg.manifest import manifest_name, batch_skip_reason
from dotpkg.options import Options
from dotpkg.resolve import cwd_dotpkgs, resolve_dotpkgs
from dotpkg.utils.log import info, warn
from dotpkg.utils.prompt import confirm

import sys

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
