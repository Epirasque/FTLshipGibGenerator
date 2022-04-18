import unittest

from skimage.io import imread

from imageProcessing.ImageProcessingUtilities import findColorInImage, areAnyVisiblePixelsOverlapping, \
    areAllVisiblePixelsContained
from unitTests.TestUtilities import imageDifferenceInPercentage, initializeLoggingForTest


class ImageAnalysisTest(unittest.TestCase):
    def setUp(self) -> None:
        initializeLoggingForTest(self)

    def test_findOriginOfTilesetImage(self):
        path = 'imageProcessing/tileset_origin/'
        sourceImage = imread(path + '/source.png')
        targetImage = imread(path + '/target.png')
        edge, edgeCoordinates = findColorInImage(sourceImage, [0, 255, 0])
        self.assertTrue(imageDifferenceInPercentage(edge, targetImage) <= 2)

    def test_someImageOverlap(self):
        path = 'imageProcessing/imageOverlapTrue/'
        imageA = imread(path + '/imageA.png')
        imageB = imread(path + '/imageB.png')
        self.assertTrue(areAnyVisiblePixelsOverlapping(imageA, imageB))

    def test_noImageOverlap(self):
        path = 'imageProcessing/imageOverlapFalse/'
        imageA = imread(path + '/imageA.png')
        imageB = imread(path + '/imageB.png')
        self.assertFalse(areAnyVisiblePixelsOverlapping(imageA, imageB))

    def test_imageIsContained(self):
        path = 'imageProcessing/imageContainedTrue/'
        innerImage = imread(path + '/innerImage.png')
        outerImage = imread(path + '/outerImage.png')
        self.assertTrue(areAllVisiblePixelsContained(innerImage, outerImage))

    def test_imageIsNotContained(self):
        path = 'imageProcessing/imageContainedFalse/'
        innerImage = imread(path + '/innerImage.png')
        outerImage = imread(path + '/outerImage.png')
        self.assertFalse(areAllVisiblePixelsContained(innerImage, outerImage))


if __name__ == '__main__':
    unittest.main()
