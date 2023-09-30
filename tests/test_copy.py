import unittest
from dotpkg.manifest.installs_v2 import InstallsEntry

from tests.fixtures import DotpkgFixture, HomeDirFixture

class TestCopy(unittest.TestCase):
    def test_copy(self):
        pkg = DotpkgFixture('copy')

        with HomeDirFixture() as home:
            with pkg.install_context(home.opts):
                self.assertFalse((home.path / 'dir').is_symlink())
                self.assertTrue((home.path / 'dir').is_dir())
                self.assertTrue((home.path / 'dir' / 'a.txt').is_file())
                self.assertTrue((home.path / 'file.txt').is_file())

                self.assertEqual(home.read_install_manifest().installs[str(pkg.path)], InstallsEntry(
                    target_dir=str(home.path),
                    src_paths=[
                        str(pkg.path / 'file.txt'),
                        str(pkg.path / 'dir'),
                    ],
                    paths=[
                        str(home.path / 'file.txt'),
                        str(home.path / 'dir'),
                    ],
                ))
                
            self.assertFalse((home.path / 'dir').exists())
            self.assertFalse((home.path / 'file.txt').exists())
            self.assertEqual(home.read_install_manifest().installs, {})

            # TODO: Test failing uninstallations (e.g. if hashes mismatch)
