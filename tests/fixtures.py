from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from dotpkg.commands import install_cmd, uninstall_cmd
from dotpkg.options import Options

TEST_ROOT = Path(__file__).resolve().parent
TEST_PKGS = TEST_ROOT / 'pkgs'

class SourcePkgFixture:
    def __init__(self, name: str):
        self.name = name
    
    @property
    def path(self) -> Path:
        return TEST_PKGS / self.name
    
    def install(self, opts: Options):
        # TODO: Split up installation into more fine-grained methods and test them here...
        install_cmd([str(self.path)], opts=opts)
    
    def uninstall(self, opts: Options):
        uninstall_cmd([str(self.path)], opts=opts)

    @contextmanager
    def install_context(self, opts: Options):
        try:
            self.install(opts)
            yield None
        finally:
            self.uninstall(opts)

class HomeDirFixture:
    def __init__(self):
        self.dir = TemporaryDirectory(prefix='dotpkg-test-home')
    
    def __enter__(self):
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any):
        self.dir.cleanup()
    
    @property
    def path(self) -> Path:
        return Path(self.dir.name)
    
    @property
    def is_empty(self) -> bool:
        return next(self.path.iterdir(), None) is None

    @property
    def opts(self) -> Options:
        return Options(
            cwd=TEST_PKGS,
            home=self.path,
        )
