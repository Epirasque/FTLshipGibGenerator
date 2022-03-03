import collections
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


class MyTestCase(unittest.TestCase):
    def test_something(self):
        standaloneFolderPath = 'sample_projects/multiUsedLayoutWithFewerGibs'
        addonFolderPath = 'sample_projects/multiUsedLayoutWithFewerGibsAsAddon'

        nrGibs = 2
        imageIdWithGibs = 3

        parameters = collections.namedtuple("parameters",
                                            """INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH ADDON_OUTPUT_FOLDERPATH SHIPS_TO_IGNORE SAVE_STANDALONE SAVE_ADDON BACKUP_STANDALONE_SEGMENTS_FOR_DEVELOPER BACKUP_STANDALONE_LAYOUTS_FOR_DEVELOPER NR_GIBS QUICK_AND_DIRTY_SEGMENT CHECK_SPECIFIC_SHIPS SPECIFIC_SHIP_NAMES LIMIT_ITERATIONS ITERATION_LIMIT""")
        coreParameters = parameters(INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH=standaloneFolderPath,
                                    ADDON_OUTPUT_FOLDERPATH=addonFolderPath, SHIPS_TO_IGNORE='unset',
                                    SAVE_STANDALONE=True, SAVE_ADDON=False,
                                    BACKUP_STANDALONE_SEGMENTS_FOR_DEVELOPER=False,
                                    BACKUP_STANDALONE_LAYOUTS_FOR_DEVELOPER=False, NR_GIBS=nrGibs,
                                    QUICK_AND_DIRTY_SEGMENT=True,
                                    CHECK_SPECIFIC_SHIPS=False, SPECIFIC_SHIP_NAMES='unset', LIMIT_ITERATIONS=False,
                                    ITERATION_LIMIT=0)

        self.resetTestResources(standaloneFolderPath, addonFolderPath, [imageIdWithGibs])

        # ACT
        startGeneratorLoop(coreParameters)

        ships = loadShipFileNames(standaloneFolderPath)
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

            searchRadius = 3

            for gib in gibs:
                img = gib['img']
                array = np.asarray(img)
                for x in range(array.shape[1]):
                    for y in range(array.shape[0]):
                        if array[y, x, 3] != 0:
                            for xSearchOffset in range(-searchRadius, searchRadius + 1):
                                xSearch = x + xSearchOffset
                                for ySearchOffset in range(-searchRadius, searchRadius + 1):
                                    ySearch = y + ySearchOffset
                                    try:
                                        if array[ySearch, xSearch, 3] == 0:
                                            if shipImage[ySearch + gib['y'], xSearch + gib['x'], 3] != 0:
                                                array[y, x, 0] = 255
                                                array[y, x, 1] = 0
                                                array[y, x, 2] = 0
                                                array[y, x, 3] = 255
                                    except:
                                        pass
                Image.fromarray(array).show()
                break
            break

            # TODO: speed up e.g. numpy vectorize
        self.assertTrue(True)

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
