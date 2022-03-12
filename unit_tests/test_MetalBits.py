import collections
import unittest

from fileHandling.ShipBlueprintLoader import loadShipFileNames
from flow.GeneratorLooper import startGeneratorLoop
from unit_tests.TestUtilities import resetTestResources, assertShipReconstructedFromGibsIsAccurateEnough


class MetalBitsTest(unittest.TestCase):
    def test_metalBitsAreHiddenInitially(self):
        # ARRANGE
        standaloneFolderPath = 'sample_projects/multiUsedLayoutWithoutAnyGibs'
        addonFolderPath = 'sample_projects/multiUsedLayoutWithoutAnyGibsAsAddon'
        nrGibs = 5

        parameters = collections.namedtuple("parameters",
                                            """INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH ADDON_OUTPUT_FOLDERPATH SHIPS_TO_IGNORE SAVE_STANDALONE SAVE_ADDON BACKUP_STANDALONE_SEGMENTS_FOR_DEVELOPER BACKUP_STANDALONE_LAYOUTS_FOR_DEVELOPER NR_GIBS QUICK_AND_DIRTY_SEGMENT GENERATE_METAL_BITS ANIMATE_METAL_BITS_FOR_DEVELOPER CHECK_SPECIFIC_SHIPS SPECIFIC_SHIP_NAMES LIMIT_ITERATIONS ITERATION_LIMIT""")
        coreParameters = parameters(INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH=standaloneFolderPath,
                                    ADDON_OUTPUT_FOLDERPATH=addonFolderPath, SHIPS_TO_IGNORE='unset',
                                    SAVE_STANDALONE=True, SAVE_ADDON=False,
                                    BACKUP_STANDALONE_SEGMENTS_FOR_DEVELOPER=False,
                                    BACKUP_STANDALONE_LAYOUTS_FOR_DEVELOPER=False, NR_GIBS=nrGibs,
                                    QUICK_AND_DIRTY_SEGMENT=False, GENERATE_METAL_BITS=True,
                                    ANIMATE_METAL_BITS_FOR_DEVELOPER=True,
                                    CHECK_SPECIFIC_SHIPS=False, SPECIFIC_SHIP_NAMES='unset', LIMIT_ITERATIONS=False,
                                    ITERATION_LIMIT=0)

        resetTestResources(standaloneFolderPath, addonFolderPath, [])

        # ACT
        startGeneratorLoop(coreParameters)

        # ASSERT
        ships = loadShipFileNames(standaloneFolderPath)
        assertShipReconstructedFromGibsIsAccurateEnough(nrGibs, ships, standaloneFolderPath, 2)


if __name__ == '__main__':
    unittest.main()
