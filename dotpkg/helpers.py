from pathlib import Path

import os
import hashlib

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
