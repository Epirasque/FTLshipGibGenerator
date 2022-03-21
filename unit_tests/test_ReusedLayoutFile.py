import copy
import unittest

import numpy as np
from PIL import Image

import Core
from fileHandling.ShipBlueprintLoader import loadShipFileNames
from fileHandling.ShipImageLoader import loadShipBaseImage
from fileHandling.ShipLayoutDao import loadShipLayout
from flow.GeneratorLooper import startGeneratorLoop
from imageProcessing.MetalBitsAttacher import uncropGibs
from metadata.GibEntryChecker import getExplosionNode
from unit_tests.TestUtilities import resetTestResources


class ReusedLayoutFileTest(unittest.TestCase):
    def test_properGibsForReusedLayoutFileForStandaloneWithoutAnyGibs(self):
        # ARRANGE
        standaloneFolderPath = 'sample_projects/multiUsedLayoutWithoutAnyGibs'
        addonFolderPath = 'sample_projects/multiUsedLayoutWithoutAnyGibsAsAddon'
        nrGibs = 2

        PARAMETERS = Core.PARAMETERS
        generatorParameters = PARAMETERS(INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH=standaloneFolderPath,
                                         ADDON_OUTPUT_FOLDERPATH=addonFolderPath, SHIPS_TO_IGNORE='unset',
                                         OUTPUT_MODE=Core.STANDALONE_MODE,
                                         BACKUP_STANDALONE_SEGMENTS_FOR_DEVELOPER=False,
                                         BACKUP_STANDALONE_LAYOUTS_FOR_DEVELOPER=False, NR_GIBS=nrGibs,
                                         QUICK_AND_DIRTY_SEGMENT=True, GENERATE_METAL_BITS=True,
                                         ANIMATE_METAL_BITS_FOR_DEVELOPER=False, ANIMATE_METAL_BITS_FPS=5.,
                                         CHECK_SPECIFIC_SHIPS=False, SPECIFIC_SHIP_NAMES='unset',
                                         LIMIT_ITERATIONS=False,
                                         ITERATION_LIMIT=0)

        resetTestResources(standaloneFolderPath, addonFolderPath, [])

        # ACT
        startGeneratorLoop(generatorParameters)

        # ASSERT
        ships = loadShipFileNames(standaloneFolderPath)
        self.assertShipReconstructedFromGibsForStandaloneIsAccurateEnough(nrGibs, ships, standaloneFolderPath,
                                                                          requiredAccuracyInPercent=2)

    def test_properGibsForReusedLayoutFileForAddonWithoutAnyGibs(self):
        # ARRANGE
        standaloneFolderPath = 'sample_projects/multiUsedLayoutWithoutAnyGibs'
        addonFolderPath = 'sample_projects/multiUsedLayoutWithoutAnyGibsAsAddon'
        nrGibs = 2

        PARAMETERS = Core.PARAMETERS
        generatorParameters = PARAMETERS(INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH=standaloneFolderPath,
                                         ADDON_OUTPUT_FOLDERPATH=addonFolderPath, SHIPS_TO_IGNORE='unset',
                                         OUTPUT_MODE=Core.ADDON_MODE,
                                         BACKUP_STANDALONE_SEGMENTS_FOR_DEVELOPER=False,
                                         BACKUP_STANDALONE_LAYOUTS_FOR_DEVELOPER=False, NR_GIBS=nrGibs,
                                         QUICK_AND_DIRTY_SEGMENT=True, GENERATE_METAL_BITS=True,
                                         ANIMATE_METAL_BITS_FOR_DEVELOPER=False, ANIMATE_METAL_BITS_FPS=5.,
                                         CHECK_SPECIFIC_SHIPS=False, SPECIFIC_SHIP_NAMES='unset',
                                         LIMIT_ITERATIONS=False, ITERATION_LIMIT=0)

        resetTestResources(standaloneFolderPath, addonFolderPath, [])

        # ACT
        startGeneratorLoop(generatorParameters)

        # ASSERT
        ships = loadShipFileNames(standaloneFolderPath)
        self.assertShipReconstructedFromGibsForAddonIsAccurateEnough(nrGibs, ships, standaloneFolderPath,
                                                                     addonFolderPath, requiredAccuracyInPercent=2)

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

    def test_properGibsForReusedLayoutFileForStandaloneWithSomeGibs(self):
        # ARRANGE
        standaloneFolderPath = 'sample_projects/multiUsedLayoutWithFewerGibs'
        addonFolderPath = 'sample_projects/multiUsedLayoutWithoutAnyGibsAsAddon'
        nrGibs = 2
        imageIdWithGibs = 3

        PARAMETERS = Core.PARAMETERS
        generatorLoopParameters = PARAMETERS(INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH=standaloneFolderPath,
                                             ADDON_OUTPUT_FOLDERPATH=addonFolderPath, SHIPS_TO_IGNORE='unset',
                                             OUTPUT_MODE=Core.STANDALONE_MODE,
                                             BACKUP_STANDALONE_SEGMENTS_FOR_DEVELOPER=False,
                                             BACKUP_STANDALONE_LAYOUTS_FOR_DEVELOPER=False, NR_GIBS=nrGibs,
                                             QUICK_AND_DIRTY_SEGMENT=True, GENERATE_METAL_BITS=True,
                                             ANIMATE_METAL_BITS_FOR_DEVELOPER=False, ANIMATE_METAL_BITS_FPS=5.,
                                             CHECK_SPECIFIC_SHIPS=False, SPECIFIC_SHIP_NAMES='unset',
                                             LIMIT_ITERATIONS=False,
                                             ITERATION_LIMIT=0)

        resetTestResources(standaloneFolderPath, addonFolderPath, [imageIdWithGibs])

        # ACT
        startGeneratorLoop(generatorLoopParameters)

        # ASSERT
        ships = loadShipFileNames(standaloneFolderPath)
        self.assertShipReconstructedFromGibsForStandaloneIsAccurateEnough(nrGibs, ships, standaloneFolderPath,
                                                                          requiredAccuracyInPercent=2)

    def test_properGibsForReusedLayoutFileForAddonWithSomeGibs(self):
        # ARRANGE
        standaloneFolderPath = 'sample_projects/multiUsedLayoutWithFewerGibs'
        addonFolderPath = 'sample_projects/multiUsedLayoutWithoutAnyGibsAsAddon'
        nrGibs = 2
        imageIdWithGibs = 3

        PARAMETERS = Core.PARAMETERS
        generatorLoopParameters = PARAMETERS(INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH=standaloneFolderPath,
                                             ADDON_OUTPUT_FOLDERPATH=addonFolderPath, SHIPS_TO_IGNORE='unset',
                                             OUTPUT_MODE=Core.ADDON_MODE,
                                             BACKUP_STANDALONE_SEGMENTS_FOR_DEVELOPER=False,
                                             BACKUP_STANDALONE_LAYOUTS_FOR_DEVELOPER=False, NR_GIBS=nrGibs,
                                             QUICK_AND_DIRTY_SEGMENT=True, GENERATE_METAL_BITS=True,
                                             ANIMATE_METAL_BITS_FOR_DEVELOPER=False, ANIMATE_METAL_BITS_FPS=5.,
                                             CHECK_SPECIFIC_SHIPS=False, SPECIFIC_SHIP_NAMES='unset',
                                             LIMIT_ITERATIONS=False,
                                             ITERATION_LIMIT=0)

        resetTestResources(standaloneFolderPath, addonFolderPath, [imageIdWithGibs])

        # ACT
        startGeneratorLoop(generatorLoopParameters)

        # ASSERT
        ships = loadShipFileNames(standaloneFolderPath)
        self.assertShipReconstructedFromGibsForAddonIsAccurateEnough(nrGibs, ships, standaloneFolderPath,
                                                                     addonFolderPath, requiredAccuracyInPercent=2)

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

    def assertShipReconstructedFromGibsForStandaloneIsAccurateEnough(self, nrGibs, ships, standaloneFolderPath,
                                                                     requiredAccuracyInPercent):
        for name, filenames in ships.items():
            shipImageName = filenames['img']
            layoutName = filenames['layout']
            gibs = self.loadGibsForStandalone(layoutName, nrGibs, shipImageName, standaloneFolderPath)

            shipImage, shipImageSubfolder = loadShipBaseImage(shipImageName, standaloneFolderPath)
            highlightingImage, percentage, reconstructedFromGibs = self.reconstructFromGibs(gibs, layoutName, shipImage,
                                                                                            shipImageName)

            if percentage >= requiredAccuracyInPercent:
                Image.fromarray(highlightingImage).save('delta.png')
                reconstructedFromGibs.save('reconstructed.png')
                Image.fromarray(shipImage).save('original.png')

            self.assertTrue(percentage <= requiredAccuracyInPercent)

            self.assertGibsDoNotShareTooManyIdenticalPixels(gibs, shipImage, requiredAccuracyInPercent)

    def loadGibsForStandalone(self, layoutName, nrGibs, shipImageName, standaloneFolderPath):
        layout = loadShipLayout(layoutName, standaloneFolderPath)
        explosionNode = getExplosionNode(layout)
        gibs = []
        for gibId in range(1, nrGibs + 1):
            gibNode = explosionNode.find('gib%u' % gibId)
            gib = {}
            gib['x'] = int(gibNode.find('x').text)
            gib['y'] = int(gibNode.find('y').text)
            gib['img'] = np.asarray(Image.open(
                standaloneFolderPath + '/img/ship/' + shipImageName + '_gib' + str(gibId) + '.png'), dtype=np.uint8)
            gibs.append(gib)
        return gibs

    def reconstructFromGibs(self, gibs, layoutName, shipImage, shipImageName):
        reconstructedFromGibs = Image.fromarray(np.zeros(shipImage.shape, dtype=np.uint8))
        for gib in gibs:
            gibImage = Image.fromarray(gib['img'])
            reconstructedFromGibs.paste(gibImage, (gib['x'], gib['y']), gibImage)
        differentTransparencyPixels = abs(shipImage - reconstructedFromGibs)[:, :, 3] > 0
        percentage = 100. * differentTransparencyPixels.sum() / (shipImage.shape[0] * shipImage.shape[1])
        print("Deviating pixels for ship %s layout %s: %u of %u (%.2f%%)" % (
            shipImageName, layoutName, differentTransparencyPixels.sum(), shipImage.shape[0] * shipImage.shape[1],
            percentage))
        highlightingImage = np.zeros(shipImage.shape, dtype=np.uint8)
        highlightingImage[differentTransparencyPixels] = (255, 0, 0, 255)
        return highlightingImage, percentage, reconstructedFromGibs

    def assertShipReconstructedFromGibsForAddonIsAccurateEnough(self, nrGibs, ships, standaloneFolderPath,
                                                                addonFolderPath, requiredAccuracyInPercent):
        for name, filenames in ships.items():
            shipImageName = filenames['img']
            layoutName = filenames['layout']
            gibs = self.loadsGibsForAddon(addonFolderPath, layoutName, nrGibs, shipImageName)
            shipImage, shipImageSubfolder = loadShipBaseImage(shipImageName, standaloneFolderPath)
            highlightingImage, percentage, reconstructedFromGibs = self.reconstructFromGibs(gibs, layoutName, shipImage,
                                                                                            shipImageName)

            if percentage >= requiredAccuracyInPercent:
                Image.fromarray(highlightingImage).save('delta.png')
                reconstructedFromGibs.save('reconstructed.png')
                Image.fromarray(shipImage).save('original.png')

            self.assertTrue(percentage <= requiredAccuracyInPercent)

            self.assertGibsDoNotShareTooManyIdenticalPixels(gibs, shipImage, requiredAccuracyInPercent)

    def loadsGibsForAddon(self, addonFolderPath, layoutName, nrGibs, shipImageName):
        appendLayoutFilepath = addonFolderPath + '/data/' + layoutName + '.xml.append'
        with open(appendLayoutFilepath) as appendFile:
            lines = appendFile.readlines()
        gibs = []
        for line in lines:
            for gibId in range(1, nrGibs + 1):
                if '<mod-overwrite:gib%u>' % gibId in line:
                    gib = {}
                    gib['img'] = np.asarray(Image.open(
                        addonFolderPath + '/img/ship/' + shipImageName + '_gib' + str(gibId) + '.png'), dtype=np.uint8)
            if '<x>' in line:
                gib['x'] = int(
                    line.replace('<x>', '').replace('</x>', '').replace('\t', '').replace('\n', '').strip())
            if '<y>' in line:
                gib['y'] = int(
                    line.replace('<y>', '').replace('</y>', '').replace('\t', '').replace('\n', '').strip())
                gibs.append(gib)
        return gibs

    def assertGibsDoNotShareTooManyIdenticalPixels(self, gibs, shipImage, allowedOverlapPercentage):
        uncroppedGibs = copy.deepcopy(gibs)
        uncropGibs(uncroppedGibs, shipImage)
        for gibA in uncroppedGibs:
            # signed integer needed for abs
            imageArrayA = gibA['img']
            for gibB in uncroppedGibs:
                imageArrayB = gibB['img']
                if not imageArrayA is imageArrayB:
                    nrIdenticalPixels = 0
                    for y in range(shipImage.shape[0]):
                        for x in range(shipImage.shape[1]):
                            # TODO: RESUME HERE: then put gibs without metal bits in layout cache to get test green
                            if imageArrayA[y, x][3] == 255 and imageArrayB[y, x][3] == 255:
                                # if abs(imageArrayA[y,x][0] - imageArrayB[y,x][0]) <= 0:
                                if imageArrayA[y, x][0] == imageArrayB[y, x][0]:
                                    if imageArrayA[y, x][1] == imageArrayB[y, x][1]:
                                        if imageArrayA[y, x][2] == imageArrayB[y, x][2]:
                                            nrIdenticalPixels += 1
                    percentage = 100. * nrIdenticalPixels / (shipImage.shape[0] * shipImage.shape[1])
                    print("Deviating pixels for gib-pair: %u of %u (%.2f%%)" % (
                        nrIdenticalPixels, shipImage.shape[0] * shipImage.shape[1], percentage))
                    self.assertTrue(percentage <= allowedOverlapPercentage)


if __name__ == '__main__':
    unittest.main()
