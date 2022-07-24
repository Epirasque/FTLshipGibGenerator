import unittest

from fileHandling.ShipBlueprintLoader import loadShipFileNames
from unitTests.TestUtilities import initializeLoggingForTest


class LoadShipBlueprintsTest(unittest.TestCase):
    def setUp(self) -> None:
        initializeLoggingForTest(self)

    def test_loadShipBlueprintsWithXmlAndFtlTagsWithoutErrors(self):
        ships, layoutUsages = loadShipFileNames('sampleProjects/XML_and_FTL_tags')
        self.assertCorrectShipNames(ships)
        self.assertCorrectLayoutUsages(layoutUsages)

    def test_loadShipBlueprintsWithXmlTagsWithoutErrors(self):
        ships, layoutUsages = loadShipFileNames('sampleProjects/XML_tags')
        self.assertCorrectShipNames(ships)
        self.assertCorrectLayoutUsages(layoutUsages)

    def test_loadShipBlueprintsWithFtlTagsWithoutErrors(self):
        ships, layoutUsages = loadShipFileNames('sampleProjects/FTL_tags')
        self.assertCorrectShipNames(ships)
        self.assertCorrectLayoutUsages(layoutUsages)

    def test_loadShipBlueprintsWithNoTagsWithoutErrors(self):
        ships, layoutUsages = loadShipFileNames('sampleProjects/no_tags')
        self.assertCorrectShipNames(ships)
        self.assertCorrectLayoutUsages(layoutUsages)

    def assertCorrectShipNames(self, ships):
        assert len(ships) == 3
        assert 'TEST_SHIP1' in ships
        assert 'TEST_SHIP2' in ships
        assert 'TEST_SHIP3' in ships

    def assertCorrectLayoutUsages(self, layoutUsages):
        assert len(layoutUsages) == 2
        assert layoutUsages['test_layoutA'] == 1
        assert layoutUsages['test_layoutB'] == 2


if __name__ == '__main__':
    unittest.main()
