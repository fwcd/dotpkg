import unittest

from dotpkg.manifest.alias import CurrentInstallsEntry

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

                self.assertEqual(home.read_install_manifest().installs[str(pkg.path)], CurrentInstallsEntry(
                    target_dir=str(home.path),
                    src_paths=[
                        str(pkg.path / 'dir'),
                        str(pkg.path / 'file.txt'),
                    ],
                    paths=[
                        str(home.path / 'dir'),
                        str(home.path / 'file.txt'),
                    ],
                    checksums=[
                        'da0693c19c5165be4ee984300017532d43a02dd40d62058e982cd5234229fc43',
                        'cc4fafa4c90b4e4c08ade61acfa63add6a3fc31aa58d3f217eb199f557512e2a',
                    ]
                ))
                
            self.assertFalse((home.path / 'dir').exists())
            self.assertFalse((home.path / 'file.txt').exists())
            self.assertEqual(home.read_install_manifest().installs, {})

            # TODO: Test failing uninstallations (e.g. if hashes mismatch)
