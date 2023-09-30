from itertools import zip_longest
from pathlib import Path
from typing import Optional

from dotpkg.constants import INSTALL_MANIFEST_NAME, INSTALL_MANIFEST_VERSION
from dotpkg.manifest.dotpkg import DotpkgManifest
from dotpkg.manifest.installs import InstallsManifest
from dotpkg.manifest.installs_v2 import InstallsEntry, InstallsV2Manifest
from dotpkg.options import Options
from dotpkg.resolve import find_link_candidates, find_target_dir, resolve_ignores, resolve_manifest_str
from dotpkg.utils.file import path_digest, copy, move, link, touch, remove
from dotpkg.utils.log import note, warn
from dotpkg.utils.prompt import prompt, confirm

import json
import subprocess

# Installation/uninstallation

def install_path(src_path: Path, target_path: Path, should_copy: bool, opts: Options):
    if should_copy:
        copy(src_path, target_path, opts)
    else:
        link(src_path.resolve(), target_path, opts)

def install_manifest_path(opts: Options) -> Path:
    return opts.state_dir / INSTALL_MANIFEST_NAME

def read_install_manifest(opts: Options) -> InstallsV2Manifest:
    try:
        path = install_manifest_path(opts)
        with open(path, 'r') as f:
            raw_manifest = json.load(f)
            version = raw_manifest.get('version', 0)
            if version < INSTALL_MANIFEST_VERSION:
                if not confirm(f'An older install manifest with version {version} (current is {INSTALL_MANIFEST_VERSION}) exists at {install_manifest_path(opts)}, which may be incompatible with the current version. Should this be used anyway? If no, the old one will be ignored/overwritten.', opts):
                    raw_manifest['version'] = INSTALL_MANIFEST_VERSION
                else:
                    raw_manifest = None
    except FileNotFoundError:
        raw_manifest = None
    manifest = InstallsV2Manifest.from_dict(raw_manifest) if raw_manifest else InstallsV2Manifest()
    # Make sure that we don't accidentally forget to update either the type or
    # the version (Unfortunately the type checker doesn't let us use f-strings
    # such as f'InstallsV{INSTALL_MANIFEST_VERSION}' as a type, like TypeScript
    # would...)
    assert manifest.version == INSTALL_MANIFEST_VERSION
    return manifest

def write_install_manifest(manifest: InstallsManifest, opts: Options):
    path = install_manifest_path(opts)
    if path.exists():
        note(f'Updating {path}')
    else:
        print(f'Creating {path}')
    if not opts.dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(manifest.to_dict(), f, indent=2)

def run_script(name: str, src_dir: Path, manifest: DotpkgManifest, opts: Options):
    script = getattr(manifest.scripts, name)

    if script:
        description = f"'{name}' ('{script}')"
        if opts.safe_mode:
            warn(f"Skipping script {description} in safe mode")
        else:
            print(f"Running script {description}...")
            if not opts.dry_run:
                subprocess.run(script, shell=True, cwd=src_dir, check=True)

def display_caveats(manifest: DotpkgManifest):
    requires = manifest.requires
    if requires == 'logout':
        warn(f'{manifest.name} requires logging out and back in to apply!')
    elif requires == 'reboot':
        warn(f'{manifest.name} requires rebooting the computer to apply!')

def install(src_dir: Path, manifest: DotpkgManifest, opts: Options):
    target_dir = find_target_dir(manifest, opts)

    install_manifest = read_install_manifest(opts)
    installs = {**install_manifest.installs}
    install_key = str(src_dir)

    if install_key in installs:
        existing_install = installs[install_key]
        existing_paths = [Path(path) for path in existing_install.paths]
        existing_target_dir = Path(existing_install.target_dir or str(target_dir))
        if confirm(f'The dotpkg {install_key} is already installed to {existing_target_dir} and currently targets {target_dir}. Should it be uninstalled first?', opts):
            uninstall(src_dir, manifest, opts)
        elif target_dir.resolve() != existing_target_dir.resolve():
            warn('\n'.join([
                f'This will leave the installed files at the old target dir {existing_target_dir} orphaned, since the install for {install_key} in {install_manifest_path(opts)} will be repointed to {target_dir}. These files are affected:',
                *[f'  {path}' for path in existing_paths],
            ]))

    run_script('preinstall', src_dir, manifest, opts)

    scripts_only = manifest.is_scripts_only
    src_paths: list[Path] = []
    installed_paths: list[Path] = []

    if not scripts_only:
        target_dir.mkdir(parents=True, exist_ok=True)

        touch_files: list[str] = manifest.touch_files
        for rel_path in touch_files:
            touch_path = target_dir / rel_path
            touch(touch_path, opts)

        ignores = resolve_ignores(src_dir, manifest, opts)
        renames = manifest.renames
        should_copy = manifest.copy

        def renamer(name: str) -> str:
            for pat, s in renames.items():
                name = name.replace(resolve_manifest_str(pat, opts), resolve_manifest_str(s, opts))
            return name

        for src_path, target_path in find_link_candidates(src_dir, target_dir, renamer):
            if src_path in ignores:
                note(f'Ignoring {src_path}')
                continue

            skipped = False

            if target_path.is_symlink() or target_path.exists():
                if should_copy:
                    if path_digest(target_path) == path_digest(src_path):
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
                    # TODO: Add option to view the file e.g. with an editor if its a regular file
                    #       and show non-dotpkg symlink destination otherwise.
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
        installs[install_key] = InstallsEntry(
            target_dir=str(target_dir),
            src_paths=[str(path) for path in src_paths],
            paths=[str(path) for path in installed_paths],
        )
        install_manifest.installs = installs
        write_install_manifest(install_manifest, opts)
    
    display_caveats(manifest)

def uninstall(src_dir: Path, manifest: DotpkgManifest, opts: Options):
    install_manifest = read_install_manifest(opts)
    installs = {**install_manifest.installs}
    install_key = str(src_dir)
    install: Optional[InstallsEntry] = installs.get(install_key)

    run_script('preuninstall', src_dir, manifest, opts)
    run_script('uninstall', src_dir, manifest, opts)

    scripts_only = manifest.is_scripts_only

    if not scripts_only:
        target_dir = Path(install.target_dir) if install else find_target_dir(manifest, opts)
        should_copy = manifest.copy

        if install:
            paths = zip_longest(map(Path, install.src_paths), map(Path, install.paths), fillvalue=None)
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

                target_hash = path_digest(target_path)
                src_hash = path_digest(src_path)

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
        install_manifest.installs = installs
        write_install_manifest(install_manifest, opts)

    display_caveats(manifest)
