import unittest

from tests.fixtures import DotpkgFixture, HomeDirFixture

class TestMinimal(unittest.TestCase):
    def test_minimal(self):
        pkg = DotpkgFixture('minimal')

        with HomeDirFixture() as home:
            with pkg.install_context(home.opts):
                self.assertTrue((home.path / 'hello.txt').is_symlink())

            self.assertFalse((home.path / 'hello.txt').exists())
            self.assertEqual(home.read_install_manifest().installs, {})
