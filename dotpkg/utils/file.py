from pathlib import Path
from typing import ByteString, Protocol

from dotpkg.options import Options

import os
import hashlib
import shutil

def relativize(path: Path, base_path: Path) -> Path:
    # We use os.path.relpath instead of Path.relative_to since
    # it works too if the base_path is not an ancestor of path
    # (by inserting '..' as needed).
    return Path(os.path.relpath(str(path), str(base_path)))

class Hash(Protocol):
    '''Protocol for hash functions.'''
    def update(self, data: ByteString, /) -> None:
        raise NotImplementedError()

def hash_file(path: Path, hash: Hash):
    # https://stackoverflow.com/a/44873382
    b = bytearray(128 * 1024)
    mv = memoryview(b)
    with open(path, 'rb') as f:
        while n := f.readinto(mv):
            hash.update(mv[:n])

def hash_dir(path: Path, hash: Hash):
    for child in path.iterdir():
        hash.update(path.name.encode('utf-8'))
        hash_path(child, hash)

def hash_path(path: Path, hash: Hash):
    if path.is_dir():
        hash_dir(path, hash)
    else:
        hash_file(path, hash)

def path_digest(path: Path) -> str:
    hash = hashlib.sha256()
    hash_path(path, hash)
    return hash.hexdigest()

def copy(src_path: Path, target_path: Path, opts: Options):
    print(f'Copying {src_path} to {target_path}')
    if not opts.dry_run:
        if src_path.is_dir():
            shutil.copytree(src_path, target_path)
        else:
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
    if target_path.is_dir():
        print(f'Removing directory {target_path}')
        if not opts.dry_run:
            shutil.rmtree(target_path)
    else:
        print(f'Removing {target_path}')
        if not opts.dry_run:
            target_path.unlink()
