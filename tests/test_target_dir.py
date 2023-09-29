import unittest

from tests.fixtures import SourcePkgFixture, HomeDirFixture

class TestTargetDir(unittest.TestCase):
    def test_target_dir(self):
        pkg = SourcePkgFixture('target-dir')

        with HomeDirFixture() as home:
            with pkg.install_context(home.opts):
                path = home.path / '.config' / 'someapp'
                file_path = path / 'someconfig.json'

                self.assertTrue(path.is_dir())
                self.assertTrue(file_path.is_symlink())
                self.assertEqual(file_path.resolve(), pkg.path / file_path.name)
