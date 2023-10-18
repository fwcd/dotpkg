from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from dotpkg.commands import upgrade_install_manifest_cmd
from dotpkg.install import install, read_install_manifest, uninstall
from dotpkg.manifest.installs import InstallsManifest
from dotpkg.model import Dotpkg, DotpkgRef
from dotpkg.options import Options

TEST_ROOT = Path(__file__).resolve().parent
TEST_PKGS = TEST_ROOT / 'pkgs'

class DotpkgFixture:
    def __init__(self, name: str):
        self.name = name
    
    @property
    def path(self) -> Path:
        return TEST_PKGS / self.name
    
    @property
    def dotpkg(self) -> Dotpkg:
        return DotpkgRef(self.path).read()
    
    def install(self, opts: Options):
        install(self.dotpkg, opts=opts)
    
    def uninstall(self, opts: Options):
        uninstall(self.dotpkg, opts=opts)

    @contextmanager
    def install_context(self, opts: Options):
        self.install(opts)
        try:
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
        return Path(self.dir.name).resolve()
    
    @property
    def is_empty(self) -> bool:
        return next(self.path.iterdir(), None) is None

    @property
    def opts(self) -> Options:
        return Options(
            cwd=TEST_PKGS,
            home=self.path,
        )
    
    def upgrade_install_manifest(self):
        upgrade_install_manifest_cmd([], self.opts)
    
    def read_install_manifest(self) -> InstallsManifest:
        return read_install_manifest(self.opts)
