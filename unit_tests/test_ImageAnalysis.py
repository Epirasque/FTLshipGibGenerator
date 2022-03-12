import unittest

import imageio
from PIL import Image

from imageProcessing.ImageProcessingUtilities import findColorInImage
from unit_tests.TestUtilities import imageDifferenceInPercentage


class ImageAnalysisTest(unittest.TestCase):
    def test_findOriginOfTilesetImage(self):
        path = 'transformations/tileset_origin/'
        sourceImage = imageio.imread(path + '/source.png')
        targetImage = imageio.imread(path + '/target.png')
        edge, edgeCoordinates = findColorInImage(sourceImage, [0, 255, 0])
        self.assertTrue(imageDifferenceInPercentage(edge, targetImage) <= 2)

if __name__ == '__main__':
    unittest.main()
