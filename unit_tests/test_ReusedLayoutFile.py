import collections
import copy
import unittest

import numpy as np
from PIL import Image

import Core
from fileHandling.ShipBlueprintLoader import loadShipFileNames
from fileHandling.ShipImageLoader import loadShipBaseImage
from fileHandling.ShipLayoutDao import loadShipLayout
from flow.GeneratorLooper import startGeneratorLoop
from metadata.GibEntryChecker import getExplosionNode
from unit_tests.TestUtilities import resetTestResources


class ReusedLayoutFileTest(unittest.TestCase):
    def test_properCoordinatesForReusedLayoutFileWithoutAnyGibsForStandalone(self):
        # ARRANGE
        standaloneFolderPath = 'sample_projects/multiUsedLayoutWithoutAnyGibs'
        addonFolderPath = 'sample_projects/multiUsedLayoutWithoutAnyGibsAsAddon'
        nrGibs = 2

        PARAMETERS = collections.namedtuple("PARAMETERS",
                                            """INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH ADDON_OUTPUT_FOLDERPATH SHIPS_TO_IGNORE SAVE_STANDALONE SAVE_ADDON BACKUP_STANDALONE_SEGMENTS_FOR_DEVELOPER BACKUP_STANDALONE_LAYOUTS_FOR_DEVELOPER NR_GIBS QUICK_AND_DIRTY_SEGMENT GENERATE_METAL_BITS ANIMATE_METAL_BITS_FOR_DEVELOPER CHECK_SPECIFIC_SHIPS SPECIFIC_SHIP_NAMES LIMIT_ITERATIONS ITERATION_LIMIT""")
        coreParameters = PARAMETERS(INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH=standaloneFolderPath,
                                    ADDON_OUTPUT_FOLDERPATH=addonFolderPath, SHIPS_TO_IGNORE='unset',
                                    SAVE_STANDALONE=True, SAVE_ADDON=False,
                                    BACKUP_STANDALONE_SEGMENTS_FOR_DEVELOPER=False,
                                    BACKUP_STANDALONE_LAYOUTS_FOR_DEVELOPER=False, NR_GIBS=nrGibs,
                                    QUICK_AND_DIRTY_SEGMENT=True, GENERATE_METAL_BITS=False,
                                    ANIMATE_METAL_BITS_FOR_DEVELOPER=False, CHECK_SPECIFIC_SHIPS=False,
                                    SPECIFIC_SHIP_NAMES='unset', LIMIT_ITERATIONS=False,
                                    ITERATION_LIMIT=0)

        resetTestResources(standaloneFolderPath, addonFolderPath, [])

        # ACT
        startGeneratorLoop(coreParameters)

        # ASSERT
        ships = loadShipFileNames(standaloneFolderPath)
        self.assertShipReconstructedFromGibsIsAccurateEnoughForStandalone(nrGibs, ships, standaloneFolderPath,
                                                                          requiredAccuracyInPercent=2)

    def test_properCoordinatesForReusedLayoutFileWithoutAnyGibsForAddon(self):
        # ARRANGE
        standaloneFolderPath = 'sample_projects/multiUsedLayoutWithoutAnyGibs'
        addonFolderPath = 'sample_projects/multiUsedLayoutWithoutAnyGibsAsAddon'
        nrGibs = 2

        PARAMETERS = collections.namedtuple("PARAMETERS",
                                            """INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH ADDON_OUTPUT_FOLDERPATH SHIPS_TO_IGNORE SAVE_STANDALONE SAVE_ADDON BACKUP_STANDALONE_SEGMENTS_FOR_DEVELOPER BACKUP_STANDALONE_LAYOUTS_FOR_DEVELOPER NR_GIBS QUICK_AND_DIRTY_SEGMENT GENERATE_METAL_BITS ANIMATE_METAL_BITS_FOR_DEVELOPER CHECK_SPECIFIC_SHIPS SPECIFIC_SHIP_NAMES LIMIT_ITERATIONS ITERATION_LIMIT""")
        coreParameters = PARAMETERS(INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH=standaloneFolderPath,
                                    ADDON_OUTPUT_FOLDERPATH=addonFolderPath, SHIPS_TO_IGNORE='unset',
                                    SAVE_STANDALONE=False, SAVE_ADDON=True,
                                    BACKUP_STANDALONE_SEGMENTS_FOR_DEVELOPER=False,
                                    BACKUP_STANDALONE_LAYOUTS_FOR_DEVELOPER=False, NR_GIBS=nrGibs,
                                    QUICK_AND_DIRTY_SEGMENT=True, GENERATE_METAL_BITS=False,
                                    ANIMATE_METAL_BITS_FOR_DEVELOPER=False, CHECK_SPECIFIC_SHIPS=False,
                                    SPECIFIC_SHIP_NAMES='unset', LIMIT_ITERATIONS=False,
                                    ITERATION_LIMIT=0)

        resetTestResources(standaloneFolderPath, addonFolderPath, [])

        # ACT
        startGeneratorLoop(coreParameters)

        # ASSERT
        ships = loadShipFileNames(standaloneFolderPath)
        self.assertShipReconstructedFromGibsIsAccurateEnoughForStandalone(nrGibs, ships, standaloneFolderPath,
                                                                          requiredAccuracyInPercent=2)

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

    def test_properCoordinatesForReusedLayoutFileWithSomeGibsForStandalone(self):
        # ARRANGE
        standaloneFolderPath = 'sample_projects/multiUsedLayoutWithFewerGibs'
        addonFolderPath = 'sample_projects/multiUsedLayoutWithoutAnyGibsAsAddon'
        nrGibs = 2
        imageIdWithGibs = 3

        PARAMETERS = Core.PARAMETERS
        generatorLoopParameters = PARAMETERS(INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH=standaloneFolderPath,
                                             ADDON_OUTPUT_FOLDERPATH=addonFolderPath, SHIPS_TO_IGNORE='unset',
                                             SAVE_STANDALONE=True, SAVE_ADDON=False,
                                             BACKUP_STANDALONE_SEGMENTS_FOR_DEVELOPER=False,
                                             BACKUP_STANDALONE_LAYOUTS_FOR_DEVELOPER=False, NR_GIBS=nrGibs,
                                             QUICK_AND_DIRTY_SEGMENT=True, GENERATE_METAL_BITS=False,
                                             ANIMATE_METAL_BITS_FOR_DEVELOPER=False, ANIMATE_METAL_BITS_FPS=5.,
                                             CHECK_SPECIFIC_SHIPS=False, SPECIFIC_SHIP_NAMES='unset',
                                             LIMIT_ITERATIONS=False,
                                             ITERATION_LIMIT=0)

        resetTestResources(standaloneFolderPath, addonFolderPath, [imageIdWithGibs])

        # ACT
        startGeneratorLoop(generatorLoopParameters)

        # ASSERT
        ships = loadShipFileNames(standaloneFolderPath)
        self.assertShipReconstructedFromGibsIsAccurateEnoughForStandalone(nrGibs, ships, standaloneFolderPath,
                                                                          requiredAccuracyInPercent=2)

    def test_properCoordinatesForReusedLayoutFileWithSomeGibsForAddon(self):
        # ARRANGE
        standaloneFolderPath = 'sample_projects/multiUsedLayoutWithFewerGibs'
        addonFolderPath = 'sample_projects/multiUsedLayoutWithoutAnyGibsAsAddon'
        nrGibs = 2
        imageIdWithGibs = 3

        PARAMETERS = Core.PARAMETERS
        generatorLoopParameters = PARAMETERS(INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH=standaloneFolderPath,
                                             ADDON_OUTPUT_FOLDERPATH=addonFolderPath, SHIPS_TO_IGNORE='unset',
                                             SAVE_STANDALONE=True, SAVE_ADDON=False,
                                             BACKUP_STANDALONE_SEGMENTS_FOR_DEVELOPER=False,
                                             BACKUP_STANDALONE_LAYOUTS_FOR_DEVELOPER=False, NR_GIBS=nrGibs,
                                             QUICK_AND_DIRTY_SEGMENT=True, GENERATE_METAL_BITS=False,
                                             ANIMATE_METAL_BITS_FOR_DEVELOPER=False, ANIMATE_METAL_BITS_FPS=5.,
                                             CHECK_SPECIFIC_SHIPS=False, SPECIFIC_SHIP_NAMES='unset',
                                             LIMIT_ITERATIONS=False,
                                             ITERATION_LIMIT=0)

        resetTestResources(standaloneFolderPath, addonFolderPath, [imageIdWithGibs])

        # ACT
        startGeneratorLoop(generatorLoopParameters)

        # ASSERT
        ships = loadShipFileNames(standaloneFolderPath)
        self.assertShipReconstructedFromGibsIsAccurateEnoughForStandalone(nrGibs, ships, standaloneFolderPath,
                                                                          requiredAccuracyInPercent=2)

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

    def assertShipReconstructedFromGibsIsAccurateEnoughForStandalone(self, nrGibs, ships, standaloneFolderPath,
                                                                     requiredAccuracyInPercent):
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
            highlightingImage, percentage, reconstructedFromGibs = self.reconstructFromGibs(gibs, layoutName, shipImage,
                                                                                            shipImageName)

            if percentage >= requiredAccuracyInPercent:
                Image.fromarray(highlightingImage).save('delta.png')
                reconstructedFromGibs.save('reconstructed.png')
                Image.fromarray(shipImage).save('original.png')

            self.assertTrue(percentage < requiredAccuracyInPercent)

    def reconstructFromGibs(self, gibs, layoutName, shipImage, shipImageName):
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
        return highlightingImage, percentage, reconstructedFromGibs

    def assertShipReconstructedFromGibsIsAccurateEnoughForAddon(self, nrGibs, ships, standaloneFolderPath,
                                                                addonFolderPath, requiredAccuracyInPercent):
        for name, filenames in ships.items():
            shipImageName = filenames['img']
            layoutName = filenames['layout']
            appendLayoutFilepath = addonFolderPath + '/data/' + layoutName + '.xml.append'
            with open(appendLayoutFilepath) as appendFile:
                lines = appendFile.readlines()
            gibs = []
            for line in lines:
                for gibId in range(1, nrGibs + 1):
                    if '<mod-overwrite:gib%u>' % gibId in line:
                        gib = {}
                        gib['img'] = Image.open(
                            addonFolderPath + '/img/ship/' + shipImageName + '_gib' + str(gibId) + '.png')
                if '<x>' in line:
                    gib['x'] = int(
                        line.replace('<x>', '').replace('</x>', '').replace('\t', '').replace('\n', '').strip())
                if '<y>' in line:
                    gib['y'] = int(
                        line.replace('<y>', '').replace('</y>', '').replace('\t', '').replace('\n', '').strip())
                    gibs.append(gib)

            shipImage, shipImageSubfolder = loadShipBaseImage(shipImageName, standaloneFolderPath)
            highlightingImage, percentage, reconstructedFromGibs = self.reconstructFromGibs(gibs, layoutName, shipImage,
                                                                                            shipImageName)

            if percentage >= requiredAccuracyInPercent:
                Image.fromarray(highlightingImage).save('delta.png')
                reconstructedFromGibs.save('reconstructed.png')
                Image.fromarray(shipImage).save('original.png')

            self.assertTrue(percentage < requiredAccuracyInPercent)


if __name__ == '__main__':
    unittest.main()
