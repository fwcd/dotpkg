from pathlib import Path
from typing import Callable, Iterable, Optional

from dotpkg.constants import IGNORED_NAMES
from dotpkg.error import NoTargetDirError
from dotpkg.manifest.dotpkg import DotpkgManifest
from dotpkg.model import Dotpkg
from dotpkg.options import Options

import platform
import shutil
import socket

# Manifest resolution

def find_link_candidates(src_dir: Path, target_dir: Path, renamer: Callable[[str], str] = lambda name: name) -> Iterable[tuple[Path, Path]]:
    for src_path in sorted(src_dir.iterdir()):
        name = renamer(src_path.name)
        target_path = target_dir / name

        if name not in IGNORED_NAMES:
            # We only descend into existing directories that are not Git repos
            if target_path.exists() and not target_path.is_symlink() and target_path.is_dir() and not (target_path / '.git').exists():
                yield from find_link_candidates(src_path, target_path)
            else:
                yield src_path, target_path

def manifest_vars(opts: Options):
    return {
        '${home}': str(opts.home.resolve()),
        '${hostname}': socket.gethostname()
    }

def resolve_manifest_str(s: str, opts: Options) -> str:
    resolved = s
    for key, value in manifest_vars(opts).items():
        resolved = resolved.replace(key, value)
    return resolved

def resolve_ignores(pkg: Dotpkg, opts: Options) -> set[Path]:
    host_specific_patterns = pkg.manifest.host_specific_files
    host_specific_includes = {
        pkg.path / resolve_manifest_str(p, opts)
        for p in host_specific_patterns
    }
    host_specific_ignores = {
        i
        for p in host_specific_patterns
        for i in pkg.path.glob(p.replace('${hostname}', '*'))
        if i not in host_specific_includes and not i.name.endswith('.private')
    }
    custom_ignores = {
        i
        for p in pkg.manifest.ignored_files
        for i in pkg.path.glob(p)
    }
    ignores = host_specific_ignores.union(custom_ignores)
    return ignores

def find_target_dir(manifest: DotpkgManifest, opts: Options) -> Path:
    raw_dirs = manifest.target_dir
    dir_paths = [Path(resolve_manifest_str(raw_dir, opts)) for raw_dir in raw_dirs]

    for path in dir_paths:
        if path.is_dir() and path.exists():
            return path

    if manifest.create_target_dir_if_needed and dir_paths:
        # Defer creation until after potentially uninstalling an old version
        return dir_paths[0]

    raise NoTargetDirError(f'No suitable targetDir found in {raw_dirs}!')

def unsatisfied_path_requirements(manifest: DotpkgManifest) -> Iterable[str]:
    for requirement in manifest.requires_on_path:
        if not shutil.which(requirement):
            yield requirement

def batch_skip_reason(manifest: DotpkgManifest, opts: Options) -> Optional[str]:
    if manifest.skip_during_batch_install:
        return f'Batch-install'

    our_platform = platform.system().lower()
    supported_platforms: set[str] = set(manifest.platforms)
    if supported_platforms and (our_platform not in supported_platforms):
        return f"Platform {our_platform} is not supported, supported {'is' if len(supported_platforms) == 1 else 'are'} {', '.join(sorted(supported_platforms))}"

    unsatisfied_reqs = list(unsatisfied_path_requirements(manifest))
    if unsatisfied_reqs:
        return f"Could not find {', '.join(unsatisfied_reqs)} on PATH"

    try:
        find_target_dir(manifest, opts)
    except NoTargetDirError as e:
        return str(e)

    return None
