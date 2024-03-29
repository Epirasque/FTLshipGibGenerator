import unittest

import Core
from fileHandling.ShipBlueprintLoader import loadShipFileNames
from flow.GeneratorLooper import startGeneratorLoop
from unitTests.TestUtilities import resetTestResources, assertShipReconstructedFromGibsIsAccurateEnough, \
    initializeLoggingForTest


class MetalBitsTest(unittest.TestCase):
    def setUp(self) -> None:
        initializeLoggingForTest(self)

    def test_metalBitsAreHiddenInitially(self):
        # ARRANGE
        standaloneFolderPath = 'sampleProjects/metalBits'
        addonFolderPath = 'unset'
        nrGibs = 5

        PARAMETERS = Core.PARAMETERS
        generatorLoopParameters = PARAMETERS(INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH=standaloneFolderPath,
                                             ADDON_OUTPUT_FOLDERPATH=addonFolderPath, SHIPS_TO_IGNORE='unset',
                                             OUTPUT_MODE=Core.STANDALONE_MODE,
                                             BACKUP_SEGMENTS_FOR_DEVELOPER=False,
                                             BACKUP_LAYOUTS_FOR_DEVELOPER=False, NR_GIBS=nrGibs,
                                             QUICK_AND_DIRTY_SEGMENT=False, GENERATE_METAL_BITS=True,
                                             ANIMATE_METAL_BITS_FOR_DEVELOPER=True, ANIMATE_METAL_BITS_FPS=5.,
                                             CHECK_SPECIFIC_SHIPS=False, SPECIFIC_SHIP_NAMES='unset',
                                             LIMIT_ITERATIONS=False,
                                             ITERATION_LIMIT=0)

        resetTestResources(standaloneFolderPath, addonFolderPath, [])

        # ACT
        startGeneratorLoop(generatorLoopParameters)

        # ASSERT
        ships, layoutUsages = loadShipFileNames(standaloneFolderPath)
        assertShipReconstructedFromGibsIsAccurateEnough(nrGibs, ships, standaloneFolderPath, 2)


if __name__ == '__main__':
    unittest.main()
