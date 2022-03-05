import collections
import copy
import os
import shutil
import unittest

import numpy as np
from PIL import Image

from fileHandling.shipBlueprintLoader import loadShipFileNames
from fileHandling.shipImageLoader import loadShipBaseImage
from fileHandling.shipLayoutDao import loadShipLayout
from flow.generatorLooper import startGeneratorLoop
from metadata.gibEntryChecker import getExplosionNode


class ReusedLayoutFileTest(unittest.TestCase):
    def test_properCoordinatesForReusedLayoutFileWithoutAnyGibs(self):
        # ARRANGE
        standaloneFolderPath = 'sample_projects/multiUsedLayoutWithoutAnyGibs'
        addonFolderPath = 'sample_projects/multiUsedLayoutWithoutAnyGibsAsAddon'
        nrGibs = 2

        parameters = collections.namedtuple("parameters",
                                            """INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH ADDON_OUTPUT_FOLDERPATH SHIPS_TO_IGNORE SAVE_STANDALONE SAVE_ADDON BACKUP_STANDALONE_SEGMENTS_FOR_DEVELOPER BACKUP_STANDALONE_LAYOUTS_FOR_DEVELOPER NR_GIBS QUICK_AND_DIRTY_SEGMENT CHECK_SPECIFIC_SHIPS SPECIFIC_SHIP_NAMES LIMIT_ITERATIONS ITERATION_LIMIT""")
        coreParameters = parameters(INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH=standaloneFolderPath,
                                    ADDON_OUTPUT_FOLDERPATH=addonFolderPath, SHIPS_TO_IGNORE='unset',
                                    SAVE_STANDALONE=True, SAVE_ADDON=True,
                                    BACKUP_STANDALONE_SEGMENTS_FOR_DEVELOPER=False,
                                    BACKUP_STANDALONE_LAYOUTS_FOR_DEVELOPER=False, NR_GIBS=nrGibs,
                                    QUICK_AND_DIRTY_SEGMENT=True,
                                    CHECK_SPECIFIC_SHIPS=False, SPECIFIC_SHIP_NAMES='unset', LIMIT_ITERATIONS=False,
                                    ITERATION_LIMIT=0)

        self.resetTestResources(standaloneFolderPath, addonFolderPath, [])

        # ACT
        startGeneratorLoop(coreParameters)

        # ASSERT
        ships = loadShipFileNames(standaloneFolderPath)
        self.assertShipReconstructedFromGibsIsAccurateEnough(nrGibs, ships, standaloneFolderPath)

        with open(addonFolderPath + '/data/test_layoutA.xml.append') as layoutA:
            content = layoutA.read()
            for gibId in range(1, nrGibs + 1):
                self.assertEqual(1, content.count('<mod-overwrite:gib%u>' % gibId))
            self.assertEqual(4, content.count('<mod:findLike type="mount">'))
        with open(addonFolderPath + '/data/test_layoutB.xml.append') as layoutA:
            content = layoutA.read()
            for gibId in range(1, nrGibs + 1):
                self.assertEqual(1, content.count('<mod-overwrite:gib%u>' % gibId))
            self.assertEqual(4, content.count('<mod:findLike type="mount">'))

    def test_properCoordinatesForReusedLayoutFileWithSomeGibs(self):
        # ARRANGE
        standaloneFolderPath = 'sample_projects/multiUsedLayoutWithFewerGibs'
        addonFolderPath = 'sample_projects/multiUsedLayoutWithoutAnyGibsAsAddon'
        nrGibs = 2
        imageIdWithGibs = 3

        parameters = collections.namedtuple("parameters",
                                            """INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH ADDON_OUTPUT_FOLDERPATH SHIPS_TO_IGNORE SAVE_STANDALONE SAVE_ADDON BACKUP_STANDALONE_SEGMENTS_FOR_DEVELOPER BACKUP_STANDALONE_LAYOUTS_FOR_DEVELOPER NR_GIBS QUICK_AND_DIRTY_SEGMENT CHECK_SPECIFIC_SHIPS SPECIFIC_SHIP_NAMES LIMIT_ITERATIONS ITERATION_LIMIT""")
        coreParameters = parameters(INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH=standaloneFolderPath,
                                    ADDON_OUTPUT_FOLDERPATH=addonFolderPath, SHIPS_TO_IGNORE='unset',
                                    SAVE_STANDALONE=True, SAVE_ADDON=True,
                                    BACKUP_STANDALONE_SEGMENTS_FOR_DEVELOPER=False,
                                    BACKUP_STANDALONE_LAYOUTS_FOR_DEVELOPER=False, NR_GIBS=nrGibs,
                                    QUICK_AND_DIRTY_SEGMENT=True,
                                    CHECK_SPECIFIC_SHIPS=False, SPECIFIC_SHIP_NAMES='unset', LIMIT_ITERATIONS=False,
                                    ITERATION_LIMIT=0)

        self.resetTestResources(standaloneFolderPath, addonFolderPath, [imageIdWithGibs])

        # ACT
        startGeneratorLoop(coreParameters)

        # ASSERT
        ships = loadShipFileNames(standaloneFolderPath)
        self.assertShipReconstructedFromGibsIsAccurateEnough(nrGibs, ships, standaloneFolderPath)

        with open(addonFolderPath + '/data/test_layoutA.xml.append') as layoutA:
            content = layoutA.read()
            for gibId in range(1, nrGibs + 1):
                self.assertEqual(1, content.count('<mod-overwrite:gib%u>' % gibId))
            self.assertEqual(4, content.count('<mod:findLike type="mount">'))
        with open(addonFolderPath + '/data/test_layoutB.xml.append') as layoutA:
            content = layoutA.read()
            for gibId in range(1, nrGibs + 1):
                self.assertEqual(1, content.count('<mod-overwrite:gib%u>' % gibId))
            self.assertEqual(4, content.count('<mod:findLike type="mount">'))

    def assertShipReconstructedFromGibsIsAccurateEnough(self, nrGibs, ships, standaloneFolderPath):
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
                with Image.open(
                        standaloneFolderPath + '/img/ship/' + shipImageName + '_gib' + str(gibId) + '.png') as gibImage:
                    gib['img'] = copy.deepcopy(gibImage)
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

            self.assertTrue(percentage < 5)

    def resetTestResources(self, standaloneFolderPath, addonFolderPath, imageIdsToKeepGibsFor):
        for imageId in range(1, 4 + 1):
            if imageId in imageIdsToKeepGibsFor:
                print('Keeping gibs for image ID %u' % imageId)
                continue
            for gibId in range(1, 10 + 1):
                try:
                    os.remove(standaloneFolderPath + '/img/ship/test_image%u_gib%u.png' % (imageId, gibId))
                except:
                    pass
                try:
                    os.remove(addonFolderPath + '/img/ship/test_image%u_gib%u.png' % (imageId, gibId))
                except:
                    pass
                try:
                    os.remove(addonFolderPath + '/data/test_layoutA.xml.append')
                except:
                    pass
                try:
                    os.remove(addonFolderPath + '/data/test_layoutB.xml.append')
                except:
                    pass
        shutil.copyfile(standaloneFolderPath + '/data/TO_USE_test_layoutA.xml',
                        standaloneFolderPath + '/data/test_layoutA.xml')
        shutil.copyfile(standaloneFolderPath + '/data/TO_USE_test_layoutB.xml',
                        standaloneFolderPath + '/data/test_layoutB.xml')


if __name__ == '__main__':
    unittest.main()
