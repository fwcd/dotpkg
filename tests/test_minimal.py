import unittest

from tests.fixtures import SourcePkgFixture

class TestMinimal(unittest.TestCase):
    def test_minimal(self):
        pkg = SourcePkgFixture('minimal')
        pkg.install()
        # TODO: Add assertions
