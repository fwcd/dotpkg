import unittest

from dotpkg.manifest.alias import CurrentInstallsEntry
from dotpkg.manifest.installs_v2 import InstallsV2Manifest

from tests.fixtures import DotpkgFixture, HomeDirFixture

class TestInstallManifestUpgrade(unittest.TestCase):
    def test_v2_upgrade(self):
        pkg = DotpkgFixture('copy')

        with HomeDirFixture() as home:
            home.write_install_manifest(InstallsV2Manifest())

            with pkg.install_context(home.opts):
                self.assertEqual(home.read_install_manifest().installs[str(pkg.path)], InstallsV2Manifest.InstallsEntry(
                    target_dir=str(home.path),
                    src_paths=[
                        str(pkg.path / 'dir'),
                        str(pkg.path / 'file.txt'),
                    ],
                    paths=[
                        str(home.path / 'dir'),
                        str(home.path / 'file.txt'),
                    ]
                ))
                home.upgrade_install_manifest()
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
                        '1d17608651772e002f2e4d0ac604d957b5b7928b6a01fc22476bf0d4acb05d79',
                        'cc4fafa4c90b4e4c08ade61acfa63add6a3fc31aa58d3f217eb199f557512e2a',
                    ]
                ))
