import copy
from copy import deepcopy

import numpy as np
from PIL import Image

from fileHandling.GibImageChecker import areGibsPresentAsImageFiles
from fileHandling.ShipImageLoader import loadShipBaseImage
from imageProcessing.ImageProcessingUtilities import cropImage
from imageProcessing.MetalBitsAttacher import attachMetalBits
from metadata.GibEntryChecker import getExplosionNode

GIB_CACHE_FOLDER = 'gibCache'


# TODO: fix redundant append gib overwrites in addon mode
# TODO: add profiling
def generateGibsBasedOnSameLayoutGibMask(PARAMETERS, tilesets, layout, layoutName, name, nrGibs, shipImageName, ships, standaloneFolderPath, targetFolderPath,
                                         layoutNameToGibCache):
    print('Gibs in layout %s but not in image %s for %s' % (layoutName, shipImageName, name))
    foundGibsSameLayout = False
    newGibsWithoutMetalBits = []
    gibsForMask = []
    newBaseImage, newShipImageSubfolder = loadShipBaseImage(shipImageName, standaloneFolderPath)
    folderPath = targetFolderPath + '/img/' + newShipImageSubfolder
    if layoutName in layoutNameToGibCache:
        print('Found gibs already generated in this run')
        shipImageNameInCache, nrGibs, layout = layoutNameToGibCache[layoutName]
        gibsForMask = loadGibs(layout, nrGibs, GIB_CACHE_FOLDER, shipImageNameInCache)
        if len(gibsForMask) == nrGibs:
            foundGibsSameLayout = True
    else:
        for searchName, searchFilenames in ships.items():
            searchShipName = searchFilenames['img']
            searchLayoutName = searchFilenames['layout']
            if searchName != name and layoutName == searchLayoutName:
                if areGibsPresentAsImageFiles(searchShipName, targetFolderPath):
                    print('Found identical layout with existing gibs for image %s' % searchShipName)
                    gibsForMask = loadGibs(layout, nrGibs, folderPath, searchShipName)
                    if len(gibsForMask) > 0:
                        foundGibsSameLayout = True
                else:
                    print('Skipping identical layout for image %s as it has no gibs either' % searchShipName)
    if foundGibsSameLayout == True:
        for gibForMask in gibsForMask:  # TODO: test case for deviating number of maskgibs
            uncroppedSearchGibImg = Image.fromarray(np.zeros(newBaseImage.shape, dtype=np.uint8))
            uncroppedSearchGibImg.paste(gibForMask['img'], (gibForMask['x'], gibForMask['y']), gibForMask['img'])
            searchGibTransparentMask = np.asarray(uncroppedSearchGibImg)[:, :, 3] == 0
            uncroppedNewGib = deepcopy(newBaseImage)
            uncroppedNewGib[searchGibTransparentMask] = (0, 0, 0, 0)

            newGib = {}
            newGib['id'] = gibForMask['id']
            newGib['x'] = gibForMask['x']
            newGib['y'] = gibForMask['y']
            newGib['img'], center, minX, minY = cropImage(uncroppedNewGib)
            newGib['center'] = center
            #newGib['x'] = minX
            #newGib['y'] = minY
            newGib['mass'] = (center['x'] - newGib['x']) * (center['y'] - newGib['y']) * 4  # TODO: reenable nrVisiblePixels
            newGibsWithoutMetalBits.append(newGib)
        if PARAMETERS.GENERATE_METAL_BITS == True:
            newGibsWithMetalBits = attachMetalBits(newGibsWithoutMetalBits, newBaseImage, tilesets, PARAMETERS, shipImageName)
    return foundGibsSameLayout, newGibsWithMetalBits, newGibsWithoutMetalBits, folderPath


# TODO: extract as class, add profiling
def loadGibs(layout, nrGibs, basePath, shipName):
    gibsForMask = []
    explosionNode = getExplosionNode(layout)  # layout is same as searchLayout
    for gibId in range(1, nrGibs + 1):
        gibNode = explosionNode.find('gib%u' % gibId)
        gibForMask = {}
        gibForMask['id'] = gibId
        gibForMask['x'] = int(gibNode.find('x').text)
        gibForMask['y'] = int(gibNode.find('y').text)
        # TODO: use nparray instead?
        with Image.open(basePath + '/' + shipName + "_gib" + str(gibId) + '.png') as gibForMaskImage:
            gibForMask['img'] = deepcopy(gibForMaskImage)
        gibsForMask.append(gibForMask)
    return gibsForMask
