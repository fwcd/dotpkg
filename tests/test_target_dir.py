import unittest

from tests.fixtures import DotpkgFixture, HomeDirFixture

class TestTargetDir(unittest.TestCase):
    def test_basic(self):
        pkg = DotpkgFixture('target-dir-basic')

        with HomeDirFixture() as home:
            with pkg.install_context(home.opts):
                path = home.path / '.config' / 'someapp'
                file_path = path / 'someconfig.json'

                self.assertTrue(path.is_dir())
                self.assertTrue(file_path.is_symlink())
                self.assertEqual(file_path.resolve(), pkg.path / file_path.name)
    
    def test_multi(self):
        pkg = DotpkgFixture('target-dir-multi')

        with HomeDirFixture() as home:
            path = home.path / '.config' / 'b'
            path.mkdir(parents=True)

            with pkg.install_context(home.opts):
                self.assertFalse((home.path / '.config' / 'a').exists())
                self.assertFalse((home.path / '.config' / 'c').exists())
                self.assertTrue(path.is_dir())
                self.assertTrue((path / 'someconfig.json').is_symlink())
