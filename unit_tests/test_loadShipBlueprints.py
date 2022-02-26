import unittest

from fileHandling.shipBlueprintLoader import loadShipFileNames


class LoadShipBlueprintsTest(unittest.TestCase):
    def test_loadShipBlueprintsWithXmlAndFtlTagsWithoutErrors(self):
        shipNames = loadShipFileNames('sample_projects/XML_and_FTL_tags')
        self.assertCorrectShipNames(shipNames)

    def test_loadShipBlueprintsWithXmlTagsWithoutErrors(self):
        shipNames = loadShipFileNames('sample_projects/XML_tags')
        self.assertCorrectShipNames(shipNames)

    def test_loadShipBlueprintsWithFtlTagsWithoutErrors(self):
        shipNames = loadShipFileNames('sample_projects/FTL_tags')
        self.assertCorrectShipNames(shipNames)

    def test_loadShipBlueprintsWithNoTagsWithoutErrors(self):
        shipNames = loadShipFileNames('sample_projects/no_tags')
        self.assertCorrectShipNames(shipNames)

    def assertCorrectShipNames(self, shipNames):
        assert len(shipNames) == 3
        assert 'TEST_SHIP1' in shipNames
        assert 'TEST_SHIP2' in shipNames
        assert 'TEST_SHIP3' in shipNames


if __name__ == '__main__':
    unittest.main()
