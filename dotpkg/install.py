from itertools import zip_longest
from pathlib import Path
from typing import Any, cast

from dotpkg.constants import INSTALL_MANIFEST_NAME
from dotpkg.error import InvalidManifestError
from dotpkg.manifest.alias import CurrentInstallsManifest
from dotpkg.manifest.dotpkg import DotpkgManifest
from dotpkg.manifest.installs import InstallsManifest
from dotpkg.manifest.installs_v1 import InstallsV1Manifest
from dotpkg.manifest.installs_v2 import InstallsV2Manifest
from dotpkg.manifest.installs_v3 import InstallsV3Manifest
from dotpkg.manifest.installs_v4 import InstallsV4Manifest
from dotpkg.model import Dotpkg
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

def read_install_manifest(opts: Options) -> InstallsManifest:
    try:
        path = install_manifest_path(opts)
        with open(path, 'r') as f:
            raw_manifest = json.load(f)
            version = raw_manifest.get('version', 0)
            match version:
                case 1: return InstallsV1Manifest.from_dict(raw_manifest)
                case 2: return InstallsV2Manifest.from_dict(raw_manifest)
                case 3: return InstallsV3Manifest.from_dict(raw_manifest)
                case 4: return InstallsV4Manifest.from_dict(raw_manifest)
                case _: raise InvalidManifestError(f'Invalid manifest version {version}')
    except FileNotFoundError:
        return CurrentInstallsManifest()

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

def run_script(name: str, pkg: Dotpkg, opts: Options):
    script = getattr(pkg.manifest.scripts, name)

    if script:
        description = f"'{name}' ('{script}')"
        if opts.safe_mode:
            warn(f"Skipping script {description} in safe mode")
        else:
            print(f"Running script {description}...")
            if not opts.dry_run:
                subprocess.run(script, shell=True, cwd=pkg.path, check=True)

def display_caveats(manifest: DotpkgManifest):
    requires = manifest.requires
    if requires == 'logout':
        warn(f'{manifest.name} requires logging out and back in to apply!')
    elif requires == 'reboot':
        warn(f'{manifest.name} requires rebooting the computer to apply!')

def install(pkg: Dotpkg, opts: Options):
    target_dir = find_target_dir(pkg.manifest, opts)

    install_manifest = read_install_manifest(opts)
    installs = {**install_manifest.installs}
    install_key = str(pkg.path)

    if install_key in installs:
        existing_install = installs[install_key]
        existing_paths = [Path(path) for path in existing_install.paths] if not isinstance(existing_install, InstallsV1Manifest.InstallsEntry) else []
        existing_target_dir = Path(existing_install.target_dir or str(target_dir))
        if confirm(f'The dotpkg {pkg.name} is already installed to {existing_target_dir} and currently targets {target_dir}. Should it be uninstalled first?', opts):
            uninstall(pkg, opts)
        elif target_dir.resolve() != existing_target_dir.resolve():
            warn('\n'.join([
                f'This will leave the installed files at the old target dir {existing_target_dir} orphaned, since the install for {install_key} in {install_manifest_path(opts)} will be repointed to {target_dir}. These files are affected:',
                *[f'  {path}' for path in existing_paths],
            ]))

    run_script('preinstall', pkg, opts)

    scripts_only = pkg.manifest.is_scripts_only
    src_paths: list[Path] = []
    installed_paths: list[Path] = []

    if not scripts_only:
        target_dir.mkdir(parents=True, exist_ok=True)

        touch_files: list[str] = pkg.manifest.touch_files
        for rel_path in touch_files:
            touch_path = target_dir / rel_path
            touch(touch_path, opts)

        ignores = resolve_ignores(pkg, opts)
        renames = pkg.manifest.renames
        should_copy = pkg.manifest.copy

        def renamer(name: str) -> str:
            for pat, s in renames.items():
                name = name.replace(resolve_manifest_str(pat, opts), resolve_manifest_str(s, opts))
            return name

        for src_path, target_path in find_link_candidates(pkg.path, target_dir, renamer):
            def record_paths():
                src_paths.append(src_path)
                installed_paths.append(target_path)

            if src_path in ignores:
                note(f'Ignoring {src_path}')
                continue

            skipped = False

            if target_path.is_symlink() or target_path.exists():
                if should_copy:
                    legacy_order = install_manifest.version <= 3
                    if path_digest(target_path, legacy_order=legacy_order) == path_digest(src_path, legacy_order=legacy_order):
                        note(f'Skipping {target_path} (target and src hashes match)')
                        record_paths()
                        continue
                else:
                    if target_path.is_symlink() and target_path.resolve() == src_path.resolve():
                        note(f'Skipping {target_path} (already linked)')
                        record_paths()
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

                def theirs():
                    move(target_path, src_path, opts)
                    install_path(src_path, target_path, should_copy, opts)

                choices = {
                    'backup': backup,
                    'overwrite': overwrite,
                    'skip': skip,
                    'theirs': theirs,
                }

                if should_copy:
                    prompt_msg = f"{target_path} exists and is not a copy of the dotpkg's file."
                else:
                    # TODO: Add option to view the file e.g. with an editor if its a regular file
                    #       and show non-dotpkg symlink destination otherwise.
                    prompt_msg = f'{target_path} exists and is not a link into the dotpkg.'

                response = prompt(prompt_msg, sorted(choices.keys()), 'backup', opts)
                choices.get(response, skip)()
                continue

            install_path(src_path, target_path, should_copy, opts)

            if not skipped:
                record_paths()
    
    run_script('install', pkg, opts)
    run_script('postinstall', pkg, opts)

    if opts.update_install_manifest:
        match install_manifest.version:
            case 1:
                installs[install_key] = InstallsV1Manifest.InstallsEntry(
                    target_dir=str(target_dir),
                )
            case 2:
                installs[install_key] = InstallsV2Manifest.InstallsEntry(
                    target_dir=str(target_dir),
                    src_paths=[str(path) for path in src_paths],
                    paths=[str(path) for path in installed_paths],
                )
            case 3:
                installs[install_key] = InstallsV3Manifest.InstallsEntry(
                    target_dir=str(target_dir),
                    src_paths=[str(path) for path in src_paths],
                    paths=[str(path) for path in installed_paths],
                    checksums=[path_digest(path, legacy_order=True) for path in installed_paths],
                )
            case 4:
                installs[install_key] = InstallsV4Manifest.InstallsEntry(
                    target_dir=str(target_dir),
                    src_paths=[str(path) for path in src_paths],
                    paths=[str(path) for path in installed_paths],
                    checksums=[path_digest(path) for path in installed_paths],
                )
        # The type checker cannot verify that this is the same manifest type. We
        # might be able to model that with "generics", i.e. type variables but
        # that would probably require splitting out the majority of this
        # function into a new one.
        install_manifest.installs = cast(Any, installs)
        write_install_manifest(install_manifest, opts)
    
    display_caveats(pkg.manifest)

def uninstall(pkg: Dotpkg, opts: Options):
    install_manifest = read_install_manifest(opts)
    installs = {**install_manifest.installs}
    install_key = str(pkg.path)
    install = installs.get(install_key)

    run_script('preuninstall', pkg, opts)
    run_script('uninstall', pkg, opts)

    scripts_only = pkg.manifest.is_scripts_only

    if not scripts_only:
        target_dir = Path(install.target_dir) if install and install.target_dir else find_target_dir(pkg.manifest, opts)
        should_copy = pkg.manifest.copy

        if install and not isinstance(install, InstallsV1Manifest.InstallsEntry):
            paths = list(zip_longest(map(Path, install.src_paths), map(Path, install.paths), fillvalue=None))
        else:
            paths = list(find_link_candidates(pkg.path, target_dir))
        
        if install and not isinstance(install, InstallsV1Manifest.InstallsEntry) and not isinstance(install, InstallsV2Manifest.InstallsEntry):
            checksums = install.checksums
        else:
            legacy_order = install_manifest.version <= 3
            checksums = [path_digest(src_path, legacy_order=legacy_order) if src_path else None for src_path, _ in paths]

        for (src_path, target_path), checksum in zip_longest(paths, checksums):
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

                if not checksum:
                    warn(f'Skipping {target_path} (missing checksum)')
                    continue
                
                if not target_path.exists():
                    warn(f'Skipping {target_path} (file does not exist)')
                    continue

                if install_manifest.version >= 4 or not target_path.is_dir():
                    target_checksum = path_digest(target_path)

                    if target_checksum != checksum:
                        note(f'Skipping {target_path} (target checksum {target_checksum} != {checksum})')
                        continue
                else:
                    warn(f'Ignoring checksum for {target_path} since the legacy directory hashes (which were generated in non-deterministic order) are unreliable, unfortunately.')
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
    
    run_script('postuninstall', pkg, opts)

    if opts.update_install_manifest and install_key in installs:
        del installs[install_key]
        # The type checker cannot verify that this is the same manifest type. We
        # might be able to model that with "generics", i.e. type variables but
        # that would probably require splitting out the majority of this
        # function into a new one.
        install_manifest.installs = cast(Any, installs)
        write_install_manifest(install_manifest, opts)

    display_caveats(pkg.manifest)
