import unittest

from dataclasses import replace
from tests.fixtures import DotpkgFixture, HomeDirFixture

class TestMinimal(unittest.TestCase):
    def setUp(self) -> None:
        self.pkg = DotpkgFixture('minimal')

    def test_with_install_manifest(self):
        with HomeDirFixture() as home:
            opts = replace(home.opts, update_install_manifest=True)

            with self.pkg.install_context(opts):
                self.assertTrue((home.path / 'hello.txt').is_symlink())

            self.assertFalse((home.path / 'hello.txt').exists())
            self.assertEqual(home.read_install_manifest().installs, {})

    def test_without_install_manifest(self):
        with HomeDirFixture() as home:
            opts = replace(home.opts, update_install_manifest=False)

            with self.pkg.install_context(opts):
                self.assertTrue((home.path / 'hello.txt').is_symlink())

            self.assertTrue(home.is_empty)
