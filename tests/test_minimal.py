import unittest

from tests.fixtures import SourcePkgFixture, HomeDirFixture

class TestMinimal(unittest.TestCase):
    def test_minimal(self):
        pkg = SourcePkgFixture('minimal')

        with HomeDirFixture() as home:
            # TODO: Move pkg.install/uninstall into a context manager?
            pkg.install(home.opts)
            self.assertTrue((home.path / 'hello.txt').is_symlink())
            pkg.uninstall(home.opts)
