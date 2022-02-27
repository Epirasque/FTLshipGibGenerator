import unittest
import os
from copy import deepcopy

import imageio
import numpy as np
import shutil
from PIL import Image
from skimage.io import imshow

from fileHandling.gibImageChecker import areGibsPresentAsImageFiles
from fileHandling.gibImageSaver import saveGibImages
from fileHandling.shipBlueprintLoader import loadShipFileNames
from fileHandling.shipImageLoader import loadShipBaseImage
from fileHandling.shipLayoutDao import loadShipLayout, saveShipLayoutStandalone
from imageProcessing.segmenter import segment, crop
from metadata.gibEntryAdder import addGibEntriesToLayout
from metadata.gibEntryChecker import areGibsPresentInLayout, getExplosionNode


class ReusedLayoutFileTest(unittest.TestCase):
    def test_properCoordinatesForReusedLayoutFile(self):
        # ARRANGE
        standaloneFolderPath = 'sample_projects/XML_and_FTL_tags'
        nrGibs = 2
        quickAndDirty = True
        for imageId in range(1, 3 + 1):
            for gibId in range(1, 10 + 1):
                try:
                    os.remove(standaloneFolderPath + '/img/ship/test_image%u_gib%u.png' % (imageId, gibId))
                except:
                    pass
        shutil.copyfile(standaloneFolderPath + '/data/TO_USE_test_layout1.xml',
                        standaloneFolderPath + '/data/test_layout1.xml')
        shutil.copyfile(standaloneFolderPath + '/data/TO_USE_test_layout2.xml',
                        standaloneFolderPath + '/data/test_layout2.xml')

        ships = loadShipFileNames(standaloneFolderPath)

        # ACT
        for name, filenames in ships.items():
            shipImageName = filenames['img']
            layoutName = filenames['layout']
            layout = loadShipLayout(layoutName, standaloneFolderPath)
            gibsInLayout = areGibsPresentInLayout(layout)
            gibsInImage = areGibsPresentAsImageFiles(shipImageName, standaloneFolderPath)
            if gibsInLayout == False or gibsInImage == False:
                if gibsInLayout == True and gibsInImage == False:
                    print('Gibs in layout %s but not in image %s for %s' % (layoutName, shipImageName, name))
                    for searchName, searchFilenames in ships.items():
                        searchShipName = searchFilenames['img']
                        searchLayoutName = searchFilenames['layout']
                        if searchName != name and layoutName == searchLayoutName:
                            print('Found identical layout with existing gibs for image %s' % searchShipName)
                            explosionNode = getExplosionNode(layout)  # layout is same as searchLayout
                            newBaseImage, irrelevantPath = loadShipBaseImage(shipImageName, standaloneFolderPath)

                            gibs = []
                            for gibId in range(1, nrGibs + 1):
                                gibNode = explosionNode.find('gib%u' % gibId)
                                gib = {}
                                gib['id'] = gibId
                                gib['x'] = int(gibNode.find('x').text)
                                gib['y'] = int(gibNode.find('y').text)
                                uncroppedSearchGibImg = Image.fromarray(np.zeros(newBaseImage.shape, dtype=np.uint8))
                                searchGibImg = Image.open(
                                    standaloneFolderPath + '/img/ship/' + searchShipName + '_gib' + str(gibId) + '.png')
                                uncroppedSearchGibImg.paste(searchGibImg, (gib['x'], gib['y']), searchGibImg)
                                searchGibTransparentMask = np.asarray(uncroppedSearchGibImg)[:, :, 3] == 0
                                uncroppedNewGib = deepcopy(newBaseImage)
                                uncroppedNewGib[searchGibTransparentMask] = (0, 0, 0, 0)

                                gib['img'], center, minX, minY = crop(uncroppedNewGib)
                                # self.assertEqual(gib['x'], minX)
                                # self.assertEqual(gib['y'], minY)
                                gibs.append(gib)
                            saveGibImages(gibs, shipImageName, shipImageSubfolder, standaloneFolderPath,
                                          developerBackup=False)  # TODO: duplicate line with below. but better to have it?
                else:
                    baseImg, shipImageSubfolder = loadShipBaseImage(shipImageName, standaloneFolderPath)
                    gibs = segment(baseImg, shipImageName, nrGibs, quickAndDirty)
                    saveGibImages(gibs, shipImageName, shipImageSubfolder, standaloneFolderPath,
                                  developerBackup=False)
                    layoutWithNewGibs = addGibEntriesToLayout(layout, gibs)
                    saveShipLayoutStandalone(layoutWithNewGibs, layoutName, standaloneFolderPath, False)

        # ASSERT
        for name, filenames in ships.items():
            shipImageName = filenames['img']
            layoutName = filenames['layout']
            layout = loadShipLayout(layoutName, standaloneFolderPath)
            explosionNode = getExplosionNode(layout)

            gibs = []
            for gibId in range(1, nrGibs + 1):
                gibNode = explosionNode.find('gib%u' % gibId)
                gib = {}
                gib['x'] = int(gibNode.find('x').text)
                gib['y'] = int(gibNode.find('y').text)
                gib['img'] = Image.open(
                    standaloneFolderPath + '/img/ship/' + shipImageName + '_gib' + str(gibId) + '.png')
                gibs.append(gib)

            shipImage, shipImageSubfolder = loadShipBaseImage(shipImageName, standaloneFolderPath)
            reconstructedFromGibs = Image.fromarray(np.zeros(shipImage.shape, dtype=np.uint8))
            for gib in gibs:
                gibImage = gib['img']
                reconstructedFromGibs.paste(gibImage, (gib['x'], gib['y']), gibImage)
            differentTransparencyPixels = abs(shipImage - reconstructedFromGibs)[:, :, 3] > 0
            percentage = 100. * differentTransparencyPixels.sum() / (shipImage.shape[0] * shipImage.shape[1])
            print("Deviating pixels for ship %s layout %s: %u of %u (%.2f%%)" % (
                shipImageName, layoutName, differentTransparencyPixels.sum(), shipImage.shape[0] * shipImage.shape[1],
                percentage))
            highlightingImage = np.zeros(shipImage.shape, dtype=np.uint8)
            highlightingImage[differentTransparencyPixels] = (255, 0, 0, 255)

            if percentage >= 5:
                Image.fromarray(highlightingImage).save('delta.png')
                reconstructedFromGibs.save('reconstructed.png')
                Image.fromarray(shipImage).save('original.png')

            self.assertTrue(percentage < 5)  # add assertion here


if __name__ == '__main__':
    unittest.main()
