import unittest

from fileHandling.shipBlueprintLoader import loadShipFileNames


class LoadShipBlueprintsTest(unittest.TestCase):
    def test_loadShipBlueprintsWithXmlAndFtlTagsWithoutErrors(self):
        loadShipFileNames('sample_projects/XML_and_FTL_tags')
    def test_loadShipBlueprintsWithXmlTagsWithoutErrors(self):
        loadShipFileNames('sample_projects/XML_tags')
    def test_loadShipBlueprintsWithFtlTagsWithoutErrors(self):
        loadShipFileNames('sample_projects/FTL_tags')
    def test_loadShipBlueprintsWithNoTagsWithoutErrors(self):
        loadShipFileNames('sample_projects/no_tags')

if __name__ == '__main__':
    unittest.main()
