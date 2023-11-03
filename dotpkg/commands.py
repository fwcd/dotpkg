from pathlib import Path

from dotpkg.constants import IGNORED_NAMES
from dotpkg.install import install, install_manifest_path, read_install_manifest, uninstall
from dotpkg.resolve import batch_skip_reason
from dotpkg.model import DotpkgRef, DotpkgRefs
from dotpkg.options import Options
from dotpkg.utils.file import move
from dotpkg.utils.log import info, warn
from dotpkg.utils.prompt import confirm

import sys

def cwd_dotpkgs(opts: Options) -> DotpkgRefs:
    cwd = opts.cwd.resolve()

    # Prefer current directory if it contains a manifest
    cwd_ref = DotpkgRef(cwd)
    if cwd_ref.manifest_path.exists():
        return DotpkgRefs(
            refs=[cwd_ref],
            is_batch=False,
        )
    
    # Otherwise resolve child directories
    return DotpkgRefs(
        refs=[
            ref
            for p in cwd.iterdir()
            for ref in [DotpkgRef(p)]
            if not p.name in IGNORED_NAMES and ref.manifest_path.exists()
        ],
        is_batch=True,
    )

def resolve_refs(raw_dotpkg_paths: list[str], opts: Options) -> DotpkgRefs:
    if raw_dotpkg_paths:
        return DotpkgRefs([DotpkgRef(Path(p).resolve()) for p in raw_dotpkg_paths], is_batch=False)
    else:
        return cwd_dotpkgs(opts)

def install_cmd(raw_dotpkg_paths: list[str], opts: Options):
    refs = resolve_refs(raw_dotpkg_paths, opts)

    if refs.is_batch and not confirm(f"Install dotpkgs {', '.join(ref.name for ref in refs)}?", opts):
        print('Cancelling')
        sys.exit(0)

    for ref in refs:
        pkg = ref.read()
        name = pkg.manifest.name

        if refs.is_batch and (skip_reason := batch_skip_reason(pkg.manifest, opts)):
            warn(f'Skipping {name} ({skip_reason})')
            continue

        info(f'Installing {name} ({pkg.manifest.description})...')
        install(pkg, opts)

def uninstall_cmd(raw_dotpkg_paths: list[str], opts: Options):
    refs = resolve_refs(raw_dotpkg_paths, opts)

    if refs.is_batch and not confirm(f"Uninstall dotpkgs {', '.join(ref.name for ref in refs)}?", opts):
        print('Cancelling')
        sys.exit(0)

    for ref in refs:
        pkg = ref.read()
        name = pkg.manifest.name

        if refs.is_batch and (skip_reason := batch_skip_reason(pkg.manifest, opts)):
            warn(f'Skipping {name} ({skip_reason})')
            continue

        info(f"Uninstalling {name} ({pkg.manifest.description})...")
        uninstall(pkg, opts)

def sync_cmd(raw_paths: list[str], opts: Options):
    uninstall_cmd(raw_paths, opts)
    install_cmd(raw_paths, opts)

def upgrade_install_manifest_cmd(unused_args: list[str], opts: Options):
    if unused_args:
        print('This command expects no arguments!')
        sys.exit(1)

    manifest = read_install_manifest(opts)
    raw_paths = list(manifest.installs.keys())

    uninstall_cmd(raw_paths, opts)

    info('Backing install manifest up and removing it')
    manifest_path = install_manifest_path(opts)
    move(manifest_path, manifest_path.with_name(f'{manifest_path.name}.v{manifest.version}.backup'), opts)

    install_cmd(raw_paths, opts)
