from itertools import zip_longest
from pathlib import Path
from typing import Callable, Iterable, Any, cast

from dotpkg.constants import IGNORED_NAMES, INSTALL_MANIFEST_PATH, INSTALL_MANIFEST_VERSION
from dotpkg.manifest import manifest_name, find_target_dir, resolve_ignores, resolve_manifest_str
from dotpkg.options import Options
from dotpkg.utils.file import file_digest, copy, move, link, touch, remove
from dotpkg.utils.log import note, warn
from dotpkg.utils.prompt import prompt, confirm

import json
import subprocess

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

def install_path(src_path: Path, target_path: Path, should_copy: bool, opts: Options):
    if should_copy:
        copy(src_path, target_path, opts)
    else:
        link(src_path, target_path, opts)

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
        INSTALL_MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
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
    install_key = str(src_dir)

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
            'targetDir': str(target_dir),
            'srcPaths': [str(path) for path in src_paths],
            'paths': [str(path) for path in installed_paths],
        }
        install_manifest['installs'] = installs
        write_install_manifest(install_manifest, opts)
    
    display_caveats(src_dir, manifest, opts)

def uninstall(src_dir: Path, manifest: dict[str, Any], opts: Options):
    install_manifest = read_install_manifest(opts)
    installs = install_manifest.get('installs', {})
    install_key = str(src_dir)
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
