import unittest

from tests.fixtures import DotpkgFixture, HomeDirFixture

class TestCopy(unittest.TestCase):
    def test_copy(self):
        pkg = DotpkgFixture('copy')

        with HomeDirFixture() as home:
            with pkg.install_context(home.opts):
                self.assertFalse((home.path / 'dir').is_symlink())
                self.assertTrue((home.path / 'dir').is_dir())
                self.assertTrue((home.path / 'dir' / 'a.txt').is_file())
            
            # FIXME: Currently the empty dir sticks around, we should fix that
            # self.assertTrue(home.is_empty)

            # TODO: Test failing uninstallations (e.g. if hashes mismatch)
