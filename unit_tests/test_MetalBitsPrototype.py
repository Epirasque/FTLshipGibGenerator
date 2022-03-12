import collections
import copy
import os
import random
import shutil
import unittest

import numpy as np
from PIL import Image
from skimage.draw import line

from fileHandling.ShipBlueprintLoader import loadShipFileNames
from fileHandling.ShipImageLoader import loadShipBaseImage
from fileHandling.ShipLayoutDao import loadShipLayout
from flow.GeneratorLooper import startGeneratorLoop
from metadata.GibEntryChecker import getExplosionNode
from unit_tests.TestUtilities import resetTestResources


class MetalBitsPrototypeTest(unittest.TestCase):
    def test_something(self):
        standaloneFolderPath = 'sample_projects/metalBits'
        addonFolderPath = 'unset'

        nrGibs = 5

        parameters = collections.namedtuple("parameters",
                                            """INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH ADDON_OUTPUT_FOLDERPATH SHIPS_TO_IGNORE SAVE_STANDALONE SAVE_ADDON BACKUP_STANDALONE_SEGMENTS_FOR_DEVELOPER BACKUP_STANDALONE_LAYOUTS_FOR_DEVELOPER NR_GIBS QUICK_AND_DIRTY_SEGMENT GENERATE_METAL_BITS CHECK_SPECIFIC_SHIPS SPECIFIC_SHIP_NAMES LIMIT_ITERATIONS ITERATION_LIMIT""")
        coreParameters = parameters(INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH=standaloneFolderPath,
                                    ADDON_OUTPUT_FOLDERPATH=addonFolderPath, SHIPS_TO_IGNORE='unset',
                                    SAVE_STANDALONE=True, SAVE_ADDON=False,
                                    BACKUP_STANDALONE_SEGMENTS_FOR_DEVELOPER=False,
                                    BACKUP_STANDALONE_LAYOUTS_FOR_DEVELOPER=False, NR_GIBS=nrGibs,
                                    QUICK_AND_DIRTY_SEGMENT=False,
                                    GENERATE_METAL_BITS = False, #YES! we do it manually in this test
                                    CHECK_SPECIFIC_SHIPS=True, SPECIFIC_SHIP_NAMES='TEST_SHIP2', LIMIT_ITERATIONS=False,
                                    ITERATION_LIMIT=0)

        resetTestResources(standaloneFolderPath, addonFolderPath, [])

        # ACT
        startGeneratorLoop(coreParameters)

        ships = loadShipFileNames(standaloneFolderPath)
        for name, filenames in ships.items():
            if coreParameters.CHECK_SPECIFIC_SHIPS == True:
                if name not in coreParameters.SPECIFIC_SHIP_NAMES:
                    continue
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

            searchRadius = 1

            for gib in gibs:
                croppedGib = gib['img']

                uncroppedGib = Image.fromarray(np.zeros(shipImage.shape, dtype=np.uint8))
                uncroppedGib.paste(croppedGib, (gib['x'], gib['y']), croppedGib)

                array = np.asarray(uncroppedGib)
                for x in range(array.shape[1]):
                    for y in range(array.shape[0]):
                        if array[y, x, 3] != 0:
                            for xSearchOffset in range(-searchRadius, searchRadius + 1):
                                xSearch = x + xSearchOffset
                                for ySearchOffset in range(-searchRadius, searchRadius + 1):
                                    ySearch = y + ySearchOffset
                                    try:
                                        if array[ySearch, xSearch, 3] == 0:
                                            # if shipImage[ySearch + gib['y'], xSearch + gib['x'], 3] != 0:
                                            if shipImage[ySearch, xSearch, 3] != 0:
                                                array[y, x, 0] = 255
                                                array[y, x, 1] = 1
                                                array[y, x, 2] = 2
                                                array[y, x, 3] = 255
                                    except:
                                        pass
                #Image.fromarray(array).show()

                nonEdgeMask = np.where(np.any(array != [255, 1, 2, 255], axis=-1))
                # straight forward inversion with ~ does not seem to work
                edgeMask = np.where(np.all(array == [255, 1, 2, 255], axis=-1))
                edge = array.copy()
                edge[nonEdgeMask] = [0, 0, 0, 0]
                # Image.fromarray(edge).show()
                edgeCoordinates = np.argwhere(edge)
                edgeCoordinates = np.delete(edgeCoordinates, 2, 1)
                edgeCoordinates = np.unique(edgeCoordinates, axis=0)
                randomPixel = edgeCoordinates[random.randint(0, edgeCoordinates.shape[0])]

                nearbyEdgePixelScanRadius = 8
                ###ellipseCoordinates = ellipse(randomPixel[0], randomPixel[1], nearbyEdgePixelScanRadius, nearbyEdgePixelScanRadius) #takes a coordinate to avoid out-of-bounds. neat.
                ###scanMask = np.zeros(array.shape)
                ###scanMask[ellipseCoordinates] = 1
                ###edgeScanPixels = array.copy()
                ###edgeScanPixels[scanMask] = [0,0,0,0]
                edgePixelsInRadius = np.zeros(array.shape, dtype=np.uint8)
                edgeCoordinatesInRadiusX = []
                edgeCoordinatesInRadiusY = []
                for edgePoint in edgeCoordinates:
                    y, x = edgePoint
                    yCenter, xCenter = randomPixel
                    if np.sqrt((xCenter - x) ** 2 + (yCenter - y) ** 2) <= nearbyEdgePixelScanRadius:
                        edgePixelsInRadius[y, x] = [1, 255, 2, 255]
                        array[y, x] = [1, 255, 2, 255]
                        edgeCoordinatesInRadiusX.append(x)
                        edgeCoordinatesInRadiusY.append(y)
                ###edgeScanPixels = array.copy()
                ###edgeScanPixels[~self.create_circular_mask(randomPixel[0], randomPixel[1], radius=nearbyEdgePixelScanRadius)] = [0,255,0,255]
                # Image.fromarray(edgePixelsInRadius).show()

                m, c = np.polyfit(edgeCoordinatesInRadiusX, edgeCoordinatesInRadiusY, deg=1)
                # lineVectorXY = (1.,m) -> https://stackoverflow.com/questions/4780119/2d-euclidean-vector-rotations
                turnedVectorYX_A = self.normalized([1., -m])[0]
                turnedVectorYX_B = self.normalized([-1., m])[0]
                scanForTransparencyDistance = 2
                # TODO: this could STILL go out of bounds in rare cases even if uncropped
                scanX_A = randomPixel[1] + round(turnedVectorYX_A[1] * scanForTransparencyDistance)
                scanY_A = randomPixel[0] + round(turnedVectorYX_A[0] * scanForTransparencyDistance)
                isAtowardsTransparency = np.asarray(uncroppedGib)[scanY_A, scanX_A][3] == 0
                scanX_B = randomPixel[1] + round(turnedVectorYX_B[1] * scanForTransparencyDistance)
                scanY_B = randomPixel[0] + round(turnedVectorYX_B[0] * scanForTransparencyDistance)
                isBtowardsTransparency = np.asarray(uncroppedGib)[scanY_B, scanX_B][3] == 0
                if isAtowardsTransparency and isBtowardsTransparency:
                    print("Warning: both normals point outwards, checking an antenna-shaped edge?")
                elif ~isAtowardsTransparency and ~isBtowardsTransparency:
                    print("Error: neither normal points outwards!")
                if isAtowardsTransparency:
                    outwardVector = turnedVectorYX_A
                else:
                    outwardVector = turnedVectorYX_B
                # TODO: consider checking both and printing a warning

                # inverse coordinate names? doesn't really matter
                lineX_A, lineY_A = line(randomPixel[1], randomPixel[0], randomPixel[1] + round(outwardVector[1] * 50),
                                        randomPixel[0] + round(outwardVector[0] * 50))
                # TODO avoid out of bounds (workaround: uncropped gib which is fine; should be basis later on anyway)
                array[lineY_A, lineX_A] = [1, 2, 255, 255]

                #Image.fromarray(array).show()
                pass
                break
            break

            # TODO: speed up e.g. numpy vectorize
        self.assertTrue(True)

    # src: https://stackoverflow.com/questions/21030391/how-to-normalize-a-numpy-array-to-a-unit-vector
    # added self
    def normalized(self, a, axis=-1, order=2):
        l2 = np.atleast_1d(np.linalg.norm(a, order, axis))
        l2[l2 == 0] = 1
        return a / np.expand_dims(l2, axis)

    # src: https://stackoverflow.com/questions/44865023/how-can-i-create-a-circular-mask-for-a-numpy-array
    # added self
    def create_circular_mask(self, h, w, center=None, radius=None):

        if center is None:  # use the middle of the image
            center = (int(w / 2), int(h / 2))
        if radius is None:  # use the smallest distance between the center and image walls
            radius = min(center[0], center[1], w - center[0], h - center[1])

        Y, X = np.ogrid[:h, :w]
        dist_from_center = np.sqrt((X - center[0]) ** 2 + (Y - center[1]) ** 2)

        mask = dist_from_center <= radius
        return mask

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
