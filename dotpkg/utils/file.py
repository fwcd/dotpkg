from pathlib import Path

from dotpkg.options import Options

import os
import hashlib
import shutil

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

def remove(target_path: Path, opts: Options):
    print(f'Removing {target_path}')
    if not opts.dry_run:
        target_path.unlink()
