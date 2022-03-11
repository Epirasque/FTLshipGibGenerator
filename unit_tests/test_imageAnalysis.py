import unittest

import imageio
from PIL import Image

from imageProcessing.imageAnalyser import filterColorInImage
from unit_tests.test_utilties import imageDifferenceInPercentage


class ImageAnaylsisTest(unittest.TestCase):
    def test_findOriginOfTilesetImage(self):
        path = 'transformations/tileset_origin/'
        sourceImage = imageio.imread(path + '/source.png')
        targetImage = imageio.imread(path + '/target.png')
        edge, edgeCoordinates = filterColorInImage(sourceImage, [0, 255, 0])
        self.assertTrue(imageDifferenceInPercentage(edge, targetImage) <= 5)  # add assertion here

if __name__ == '__main__':
    unittest.main()
