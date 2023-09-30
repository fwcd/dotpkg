from pathlib import Path
from typing import Iterable, Optional

from dotpkg.install import install, uninstall
from dotpkg.manifest.dotpkg import DotpkgManifest
from dotpkg.options import Options
from dotpkg.resolve import DotpkgRefs, cwd_dotpkgs, DotpkgRef
from dotpkg.utils.log import info, warn
from dotpkg.utils.prompt import confirm

import platform
import shutil
import sys

def unsatisfied_path_requirements(manifest: DotpkgManifest) -> Iterable[str]:
    for requirement in manifest.requires_on_path:
        if not shutil.which(requirement):
            yield requirement

def batch_skip_reason(manifest: DotpkgManifest) -> Optional[str]:
    unsatisfied_reqs = list(unsatisfied_path_requirements(manifest))
    supported_platforms: set[str] = set(manifest.platforms)
    our_platform = platform.system().lower()

    if manifest.skip_during_batch_install:
        return f'Batch-install'
    if supported_platforms and (our_platform not in supported_platforms):
        return f"Platform {our_platform} is not supported, supported are {', '.join(sorted(supported_platforms))}"
    if unsatisfied_reqs:
        return f"Could not find {', '.join(unsatisfied_reqs)} on PATH"

    return None

def resolve_refs(raw_dotpkg_paths: list[str], opts: Options) -> DotpkgRefs:
    if raw_dotpkg_paths:
        return DotpkgRefs([DotpkgRef(Path(p)) for p in raw_dotpkg_paths], is_batch=False)
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

        if refs.is_batch and (skip_reason := batch_skip_reason(pkg.manifest)):
            warn(f'Skipping {name} ({skip_reason})')
            continue

        info(f'Installing {name} ({pkg.manifest.description})...')
        install(pkg.path, pkg.manifest, opts)

def uninstall_cmd(raw_dotpkg_paths: list[str], opts: Options):
    refs = resolve_refs(raw_dotpkg_paths, opts)

    if refs.is_batch and not confirm(f"Uninstall dotpkgs {', '.join(ref.name for ref in refs)}?", opts):
        print('Cancelling')
        sys.exit(0)

    for ref in refs:
        pkg = ref.read()
        name = pkg.manifest.name

        if refs.is_batch and (skip_reason := batch_skip_reason(pkg.manifest)):
            warn(f'Skipping {name} ({skip_reason})')
            continue

        info(f"Uninstalling {name} ({pkg.manifest.description})...")
        uninstall(pkg.path, pkg.manifest, opts)

def sync_cmd(dotpkgs: list[str], opts: Options):
    uninstall_cmd(dotpkgs, opts)
    install_cmd(dotpkgs, opts)
