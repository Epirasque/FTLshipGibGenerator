import unittest

from fileHandling.ShipBlueprintLoader import loadShipFileNames
from unitTests.TestUtilities import initializeLoggingForTest


class LoadShipBlueprintsTest(unittest.TestCase):
    def setUp(self) -> None:
        initializeLoggingForTest(self)

    def test_loadShipBlueprintsWithXmlAndFtlTagsWithoutErrors(self):
        ships = loadShipFileNames('sample_projects/XML_and_FTL_tags')
        self.assertCorrectShipNames(ships)

    def test_loadShipBlueprintsWithXmlTagsWithoutErrors(self):
        ships = loadShipFileNames('sample_projects/XML_tags')
        self.assertCorrectShipNames(ships)

    def test_loadShipBlueprintsWithFtlTagsWithoutErrors(self):
        ships = loadShipFileNames('sample_projects/FTL_tags')
        self.assertCorrectShipNames(ships)

    def test_loadShipBlueprintsWithNoTagsWithoutErrors(self):
        ships = loadShipFileNames('sample_projects/no_tags')
        self.assertCorrectShipNames(ships)

    def assertCorrectShipNames(self, ships):
        assert len(ships) == 3
        assert 'TEST_SHIP1' in ships
        assert 'TEST_SHIP2' in ships
        assert 'TEST_SHIP3' in ships


if __name__ == '__main__':
    unittest.main()
