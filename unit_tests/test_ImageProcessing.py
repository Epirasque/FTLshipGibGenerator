import unittest

import imageio

from imageProcessing.ImageProcessingUtilities import findColorInImage, areVisiblePixelsOverlapping, \
    areAllVisiblePixelsContained
from unit_tests.TestUtilities import imageDifferenceInPercentage


class ImageAnalysisTest(unittest.TestCase):
    def test_findOriginOfTilesetImage(self):
        path = 'imageProcessing/tileset_origin/'
        sourceImage = imageio.imread(path + '/source.png')
        targetImage = imageio.imread(path + '/target.png')
        edge, edgeCoordinates = findColorInImage(sourceImage, [0, 255, 0])
        self.assertTrue(imageDifferenceInPercentage(edge, targetImage) <= 2)

    def test_someImageOverlap(self):
        path = 'imageProcessing/imageOverlapTrue/'
        imageA = imageio.imread(path + '/imageA.png')
        imageB = imageio.imread(path + '/imageB.png')
        self.assertTrue(areVisiblePixelsOverlapping(imageA, imageB))

    def test_noImageOverlap(self):
        path = 'imageProcessing/imageOverlapFalse/'
        imageA = imageio.imread(path + '/imageA.png')
        imageB = imageio.imread(path + '/imageB.png')
        self.assertFalse(areVisiblePixelsOverlapping(imageA, imageB))

    def test_imageIsContained(self):
        path = 'imageProcessing/imageContainedTrue/'
        innerImage = imageio.imread(path + '/innerImage.png')
        outerImage = imageio.imread(path + '/outerImage.png')
        self.assertTrue(areAllVisiblePixelsContained(innerImage, outerImage))

    def test_imageIsNotContained(self):
        path = 'imageProcessing/imageContainedFalse/'
        innerImage = imageio.imread(path + '/innerImage.png')
        outerImage = imageio.imread(path + '/outerImage.png')
        self.assertFalse(areAllVisiblePixelsContained(innerImage, outerImage))


if __name__ == '__main__':
    unittest.main()
