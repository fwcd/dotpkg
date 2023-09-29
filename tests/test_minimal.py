import unittest

from tests.fixtures import SourcePkgFixture, HomeDirFixture

class TestMinimal(unittest.TestCase):
    def test_minimal(self):
        pkg = SourcePkgFixture('minimal')

        with HomeDirFixture() as home:
            with pkg.install_context(home.opts):
                self.assertTrue((home.path / 'hello.txt').is_symlink())
            self.assertTrue(home.is_empty)
