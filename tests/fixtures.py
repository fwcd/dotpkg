from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from dotpkg.commands import install_cmd
from dotpkg.options import Options

TEST_ROOT = Path(__file__).resolve().parent
TEST_PKGS = TEST_ROOT / 'pkgs'

class SourcePkgFixture:
    def __init__(self, name: str):
        self.name = name
    
    @property
    def path(self) -> Path:
        return TEST_PKGS / self.name
    
    def install(self):
        # TODO: Improve installation testing, e.g. by making all paths customizable and by using the HomeDirFixture
        install_cmd([self.name], opts=Options(dry_run=True))

class HomeDirFixture:
    def __init__(self):
        self.dir = TemporaryDirectory(prefix='dotpkg-test-home')
    
    def __enter__(self):
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any):
        self.dir.cleanup()
