import copy
import logging.config
import os
import shutil

import numpy as np
import yaml
from PIL import Image

from fileHandling.ShipImageLoader import loadShipBaseImage
from fileHandling.ShipLayoutDao import loadShipLayout
from metadata.GibEntryChecker import getExplosionNode


def initializeLoggingForTest(test):
    with open('loggingForTests.yaml') as configFile:
        configDict = yaml.load(configFile, Loader=yaml.FullLoader)
    logging.config.dictConfig(configDict)
    logger = logging.getLogger('GLAIVE')
    logger.info('RUNNING TEST ' + str(test))

def resetTestResources(standaloneFolderPath, addonFolderPath, imageIdsToKeepGibsFor):
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


def assertShipReconstructedFromGibsIsAccurateEnough(nrGibs, ships, standaloneFolderPath, requiredAccuracyInPercent):
    isAccurateEnough = True
    for name, filenames in ships.items():
        shipImageName = filenames['img']
        layoutName = filenames['layout']
        layout = loadShipLayout(layoutName, standaloneFolderPath)
        explosionNode = getExplosionNode(layout)

        gibs = []
        # load lowest z-value first
        for gibId in range(nrGibs, 0, -1):
            gibNode = explosionNode.find('gib%u' % gibId)
            gib = {}
            gib['id'] = gibId
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
        percentage = imageDifferenceInPercentage(shipImage, reconstructedFromGibs)
        print("Deviating pixels for ship %s layout %s: %.2f%%" % (
            shipImageName, layoutName, percentage))
        highlightingImage = np.zeros(shipImage.shape, dtype=np.uint8)
        differentTransparencyPixels = abs(shipImage - reconstructedFromGibs)[:, :, 3] > 0
        highlightingImage[differentTransparencyPixels] = (255, 0, 0, 255)

        if percentage >= requiredAccuracyInPercent:
            Image.fromarray(highlightingImage).save('delta.png')
            reconstructedFromGibs.save('reconstructed.png')
            Image.fromarray(shipImage).save('original.png')

        if percentage >= requiredAccuracyInPercent:
            isAccurateEnough = False
            break
    return isAccurateEnough


def imageDifferenceInPercentage(imageA, imageB):
    differentTransparencyPixels = abs(imageA - imageB)[:, :, 3] > 0
    percentage = 100. * differentTransparencyPixels.sum() / (imageA.shape[0] * imageA.shape[1])
    print("Deviating by %u of %u pixels (%.2f%%)" % (
    differentTransparencyPixels.sum(), imageA.shape[0] * imageA.shape[1], percentage))
    return percentage
