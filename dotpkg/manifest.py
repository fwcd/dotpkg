from pathlib import Path
from typing import Any, Iterable, Optional

from dotpkg.utils.log import error

import platform
import shutil
import socket

# Manifest resolution

MANIFEST_VARS = {
    '${home}': str(Path.home().resolve()),
    '${hostname}': socket.gethostname()
}

def resolve_manifest_str(s: str) -> str:
    resolved = s
    for key, value in MANIFEST_VARS.items():
        resolved = resolved.replace(key, value)
    return resolved

def resolve_ignores(src_dir: Path, manifest: dict[str, Any]) -> set[Path]:
    host_specific_patterns = manifest.get('hostSpecificFiles', [])
    host_specific_includes = {
        src_dir / resolve_manifest_str(p)
        for p in host_specific_patterns
    }
    host_specific_ignores = {
        i
        for p in host_specific_patterns
        for i in src_dir.glob(p.replace('${hostname}', '*'))
        if i not in host_specific_includes and not i.name.endswith('.private')
    }
    custom_ignores = {
        i
        for p in manifest.get('ignoredFiles', [])
        for i in src_dir.glob(p)
    }
    ignores = host_specific_ignores.union(custom_ignores)
    return ignores

def find_target_dir(manifest: dict[str, Any]) -> Path:
    raw_dirs = manifest.get('targetDir', ['${home}'])
    dir_paths = [Path(resolve_manifest_str(raw_dir)) for raw_dir in raw_dirs]

    for path in dir_paths:
        if path.is_dir() and path.exists():
            return path

    if manifest.get('createTargetDirIfNeeded', False) and dir_paths:
        # Defer creation until after potentially uninstalling an old version
        return dir_paths[0]

    return error(f'No suitable targetDir found in {raw_dirs}!')

def unsatisfied_path_requirements(manifest: dict[str, Any]) -> Iterable[str]:
    for requirement in manifest.get('requiresOnPath', []):
        if not shutil.which(requirement):
            yield requirement

def manifest_name(path: Path, manifest: dict[str, Any]) -> str:
    return manifest.get('name', path.name)

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
