import argparse
import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import platform

from dataclasses import dataclass
from itertools import zip_longest
from pathlib import Path
from typing import Callable, Iterable, Optional, Any, cast

if sys.version_info < (3, 9):
    print('Python version >= 3.9 is required!')
    sys.exit(1)

DOTPKG_MANIFEST_NAME = 'dotpkg.json'
INSTALL_MANIFEST_DIR = Path('.').resolve()
INSTALL_MANIFEST_NAME = 'installs.json'
INSTALL_MANIFEST_PATH = INSTALL_MANIFEST_DIR / INSTALL_MANIFEST_NAME
INSTALL_MANIFEST_VERSION = 2
IGNORED_NAMES = {DOTPKG_MANIFEST_NAME, INSTALL_MANIFEST_NAME, '.git', '.gitignore', '.DS_Store'}

# Helpers

RED_COLOR = '\033[91m'
YELLOW_COLOR = '\033[93m'
BLUE_COLOR = '\033[36m'
GRAY_COLOR = '\033[90m'
GREEN_COLOR = '\033[92m'
PINK_COLOR = '\033[95m'
CLEAR_COLOR = '\033[0m'

@dataclass
class Options:
    dry_run: bool
    assume_yes: bool
    safe_mode: bool
    relative_target_path: bool
    update_install_manifest: bool

def message(msg: str, color: str):
    print(f'{color}==> {msg}{CLEAR_COLOR}')

def error(msg: str):
    message(msg, RED_COLOR)
    sys.exit(1)

def warn(msg: str):
    message(msg, YELLOW_COLOR)

def info(msg: str):
    message(msg, BLUE_COLOR)

def success(msg: str):
    message(msg, GREEN_COLOR)

def note(msg: str):
    print(f'{GRAY_COLOR}{msg}{CLEAR_COLOR}')

def prompt(msg: str, choices: list[str], default: str, opts: Options) -> str:
    if opts.assume_yes:
        return default

    aliases: dict[str, str] = {}
    option_strs: list[str] = []

    if choices:
        for choice in choices:
            i = 1
            while choice[:i] in aliases.keys():
                i += 1
            aliases[choice[:i]] = choice
            option_strs.append(f'[{choice[:i]}]{choice[i:]}')

    choices_str = f" - {', '.join(option_strs)}"
    response = input(f"{PINK_COLOR}==> {msg}{choices_str} {CLEAR_COLOR}")

    return aliases.get(response, response)

def confirm(msg: str, opts: Options) -> bool:
    response = prompt(msg, ['yes', 'no'], 'yes', opts)
    return response == 'yes'

def relativize(path: Path, base_path: Path) -> Path:
    # We use os.path.relpath instead of Path.relative_to since
    # it works too if the base_path is not an ancestor of path
    # (by inserting '..' as needed).
    return Path(os.path.relpath(str(path), str(base_path)))

def file_digest(path: Path) -> str:
    # https://stackoverflow.com/a/44873382
    h = hashlib.sha256()
    b = bytearray(128 * 1024)
    mv = memoryview(b)
    with open(path, 'rb') as f:
        while n := f.readinto(mv):
            h.update(mv[:n])
    return h.hexdigest()

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

# Installation/uninstallation

def find_link_candidates(src_dir: Path, target_dir: Path, renamer: Callable[[str], str] = lambda name: name) -> Iterable[tuple[Path, Path]]:
    for src_path in src_dir.iterdir():
        name = renamer(src_path.name)
        target_path = target_dir / name

        if name not in IGNORED_NAMES:
            # We only descend into existing directories that are not Git repos
            if target_path.exists() and not target_path.is_symlink() and target_path.is_dir() and not (target_path / '.git').exists():
                yield from find_link_candidates(src_path, target_path)
            else:
                yield src_path, target_path

def copy(src_path: Path, target_path: Path, opts: Options):
    print(f'Copying {src_path} to {target_path}')
    if not opts.dry_run:
        shutil.copy(src_path, target_path)

def move(src_path: Path, target_path: Path, opts: Options):
    print(f'Moving {src_path} to {target_path}')
    if not opts.dry_run:
        shutil.move(src_path, target_path)

def link(src_path: Path, target_path: Path, opts: Options):
    print(f'Linking {target_path} -> {src_path}')
    if not opts.dry_run:
        target_path.symlink_to(src_path)

def touch(path: Path, opts: Options):
    print(f'Touching {path}')
    if not opts.dry_run:
        path.touch()

def install_path(src_path: Path, target_path: Path, should_copy: bool, opts: Options):
    if should_copy:
        copy(src_path, target_path, opts)
    else:
        link(src_path, target_path, opts)

def remove(target_path: Path, opts: Options):
    print(f'Removing {target_path}')
    if not opts.dry_run:
        target_path.unlink()

def read_install_manifest(opts: Options) -> dict[str, Any]:
    try:
        with open(INSTALL_MANIFEST_PATH, 'r') as f:
            manifest = json.load(f)
            version = manifest.get('version', 0)
            if version < INSTALL_MANIFEST_VERSION:
                if not confirm(f'An older install manifest with version {version} (current is {INSTALL_MANIFEST_VERSION}) exists at {INSTALL_MANIFEST_PATH}, which may be incompatible with the current version. Should this be used anyway? If no, the old one will be ignored/overwritten.', opts):
                    manifest['version'] = INSTALL_MANIFEST_VERSION
                else:
                    manifest = None
    except FileNotFoundError:
        manifest = None
    return manifest or {
        '$schema': 'https://raw.githubusercontent.com/fwcd/dotpkg/main/schemas/installs.schema.json',
        'version': INSTALL_MANIFEST_VERSION,
    }

def write_install_manifest(manifest: dict[str, Any], opts: Options):
    if INSTALL_MANIFEST_PATH.exists():
        note(f'Updating {INSTALL_MANIFEST_PATH}')
    else:
        print(f'Creating {INSTALL_MANIFEST_PATH}')
    if not opts.dry_run:
        with open(INSTALL_MANIFEST_PATH, 'w') as f:
            json.dump(manifest, f, indent=2)

def run_script(name: str, src_dir: Path, manifest: dict[str, Any], opts: Options):
    script = manifest.get('scripts', {}).get(name, None)

    if script:
        description = f"'{name}' ('{script}')"
        if opts.safe_mode:
            warn(f"Skipping script {description} in safe mode")
        else:
            print(f"Running script {description}...")
            if not opts.dry_run:
                subprocess.run(script, shell=True, cwd=src_dir, check=True)

def display_caveats(src_dir: Path, manifest: dict[str, Any], opts: Options):
    requires = manifest.get('requires', None)
    if requires == 'logout':
        warn(f'{manifest_name(src_dir, manifest)} requires logging out and back in to apply!')
    elif requires == 'reboot':
        warn(f'{manifest_name(src_dir, manifest)} requires rebooting the computer to apply!')

def install(src_dir: Path, manifest: dict[str, Any], opts: Options):
    target_dir = find_target_dir(manifest)

    install_manifest = read_install_manifest(opts)
    installs = install_manifest.get('installs', {})
    install_key = str(relativize(src_dir, INSTALL_MANIFEST_DIR))

    if install_key in installs:
        existing_install = installs[install_key]
        existing_paths = [Path(path) for path in existing_install.get('paths', [])]
        existing_target_dir = Path(existing_install.get('targetDir', str(target_dir)))
        if confirm(f'The dotpkg {install_key} is already installed to {existing_target_dir} and currently targets {target_dir}. Should it be uninstalled first?', opts):
            uninstall(src_dir, manifest, opts)
        elif target_dir.resolve() != existing_target_dir.resolve():
            warn('\n'.join([
                f'This will leave the installed files at the old target dir {existing_target_dir} orphaned, since the install for {install_key} in {INSTALL_MANIFEST_PATH} will be repointed to {target_dir}. These files are affected:',
                *[f'  {path}' for path in existing_paths],
            ]))

    run_script('preinstall', src_dir, manifest, opts)

    scripts_only = manifest.get('isScriptsOnly', False)
    src_paths: list[Path] = []
    installed_paths: list[Path] = []

    if not scripts_only:
        target_dir.mkdir(parents=True, exist_ok=True)

        touch_files: list[str] = manifest.get('touchFiles', [])
        for rel_path in touch_files:
            touch_path = target_dir / rel_path
            touch(touch_path, opts)

        ignores = resolve_ignores(src_dir, manifest)
        renames = manifest.get('renames', {})
        should_copy = manifest.get('copy', False)

        def renamer(name: str) -> str:
            for pat, s in renames.items():
                name = name.replace(resolve_manifest_str(pat), resolve_manifest_str(s))
            return name

        for src_path, target_path in find_link_candidates(src_dir, target_dir, renamer):
            if src_path in ignores:
                note(f'Ignoring {src_path}')
                continue

            skipped = False

            if target_path.is_symlink() or target_path.exists():
                if should_copy:
                    if file_digest(target_path) == file_digest(src_path):
                        note(f'Skipping {target_path} (target and src hashes match)')
                        continue
                else:
                    if target_path.is_symlink() and target_path.resolve() == src_path.resolve():
                        note(f'Skipping {target_path} (already linked)')
                        continue

                def backup():
                    move(target_path, target_path.with_name(f'{target_path.name}.backup'), opts)
                    install_path(src_path, target_path, should_copy, opts)

                def overwrite():
                    remove(target_path, opts)
                    install_path(src_path, target_path, should_copy, opts)

                def skip():
                    note(f'Skipping {target_path}')
                    nonlocal skipped
                    skipped = True

                choices = {
                    'backup': backup,
                    'overwrite': overwrite,
                    'skip': skip
                }

                if should_copy:
                    prompt_msg = f"{target_path} exists and is not a copy of the dotpkg's file."
                else:
                    prompt_msg = f'{target_path} exists and is not a link into the dotpkg.'

                response = prompt(prompt_msg, sorted(choices.keys()), 'skip', opts)
                choices.get(response, skip)()
                continue

            install_path(src_path, target_path, should_copy, opts)

            if not skipped:
                src_paths.append(src_path)
                installed_paths.append(target_path)
    
    run_script('install', src_dir, manifest, opts)
    run_script('postinstall', src_dir, manifest, opts)

    if opts.update_install_manifest:
        installs[install_key] = {
            'targetDir': str(relativize(target_dir, INSTALL_MANIFEST_DIR) if opts.relative_target_path else target_dir),
            'srcPaths': [str(path) for path in src_paths],
            'paths': [str(path) for path in installed_paths],
        }
        install_manifest['installs'] = installs
        write_install_manifest(install_manifest, opts)
    
    display_caveats(src_dir, manifest, opts)

def uninstall(src_dir: Path, manifest: dict[str, Any], opts: Options):
    install_manifest = read_install_manifest(opts)
    installs = install_manifest.get('installs', {})
    install_key = str(relativize(src_dir, INSTALL_MANIFEST_DIR))
    install: dict[str, Any] = installs.get(install_key, {})

    run_script('preuninstall', src_dir, manifest, opts)
    run_script('uninstall', src_dir, manifest, opts)

    scripts_only = manifest.get('isScriptsOnly', False)

    if not scripts_only:
        target_dir = Path(install['targetDir']) if 'targetDir' in install else find_target_dir(manifest)
        should_copy = manifest.get('copy', False)

        if 'paths' in install:
            paths = zip_longest(map(Path, cast(list[str], install.get('srcPaths', []))), map(Path, install['paths']), fillvalue=None)
        else:
            paths = find_link_candidates(src_dir, target_dir)

        for src_path, target_path in paths:
            if not target_path:
                note(f'Skipping src path {src_path} (no target path)')
                continue

            # TODO: Instead of just skipping these paths (and uninstalling the package from the install manifest)
            #       we should probably prompt the user (similar to the backup/overwrite options during installation)
            #       for how to proceed.

            if should_copy:
                if not src_path:
                    note(f'Skipping {target_path} (no src path in a copy-package)')
                    continue

                if target_path.is_symlink():
                    note(f'Skipping {target_path} (is a symlink while the package is copy)')
                    continue

                target_hash = file_digest(target_path)
                src_hash = file_digest(src_path)

                if target_hash != src_hash:
                    note(f'Skipping {target_path} (target hash {target_hash} != src hash {src_hash})')
                    continue
            else:
                if not target_path.is_symlink():
                    note(f'Skipping {target_path} (not a symlink)')
                    continue
                
                if src_path:
                    target_dest = target_path.resolve()
                    src_dest = src_path.resolve()
                    
                    if target_dest != src_dest:
                        note(f'Skipping {target_path} (target dest {target_dest} != src dest {src_dest}, probably not a link into the package)')
                        continue

            remove(target_path, opts)
    
    run_script('postuninstall', src_dir, manifest, opts)

    if opts.update_install_manifest and install_key in installs:
        del installs[install_key]
        install_manifest['installs'] = installs
        write_install_manifest(install_manifest, opts)

    display_caveats(src_dir, manifest, opts)

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
