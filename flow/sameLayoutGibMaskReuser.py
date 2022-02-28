from copy import deepcopy

import numpy as np
from PIL import Image

from fileHandling.gibImageChecker import areGibsPresentAsImageFiles
from fileHandling.gibImageSaver import saveGibImages
from fileHandling.shipImageLoader import loadShipBaseImage
from imageProcessing.segmenter import crop
from metadata.gibEntryChecker import getExplosionNode


# TODO: fix redundant append gib overwrites in addon mode

def generateGibsBasedOnSameLayoutGibMask(layout, layoutName, name, nrGibs, shipImageName, ships, standaloneFolderPath,
                                         layoutNameToGibsAndSubfolder):
    print('Gibs in layout %s but not in image %s for %s' % (layoutName, shipImageName, name))
    foundGibsSameLayout = False
    newGibs = []
    gibsForMask = []
    newBaseImage, newShipImageSubfolder = loadShipBaseImage(shipImageName, standaloneFolderPath)
    if layoutName in layoutNameToGibsAndSubfolder:
        print('Found gibs already generated in this run')
        gibsForMask, shipImageSubfolder = layoutNameToGibsAndSubfolder[layoutName]
        foundGibsSameLayout = True
    else:
        for searchName, searchFilenames in ships.items():
            searchShipName = searchFilenames['img']
            searchLayoutName = searchFilenames['layout']
            if searchName != name and layoutName == searchLayoutName:
                if areGibsPresentAsImageFiles(searchShipName, newShipImageSubfolder):
                    print('Found identical layout with existing gibs for image %s' % searchShipName)
                    explosionNode = getExplosionNode(layout)  # layout is same as searchLayout
                    for gibId in range(1, nrGibs + 1):
                        gibNode = explosionNode.find('gib%u' % gibId)
                        gibForMask = {}
                        gibForMask['id'] = gibId
                        gibForMask['x'] = int(gibNode.find('x').text)
                        gibForMask['y'] = int(gibNode.find('y').text)
                        gibForMask['img'] = Image.open(
                            standaloneFolderPath + '/img/' + newShipImageSubfolder + '/' + searchShipName + '_gib' + str(
                                gibId) + '.png')
                        gibsForMask.append(gibForMask)
                        foundGibsSameLayout = True
                else:
                    print('Skipping identical layout for image %s as it has no gibs either' % searchShipName)
    if foundGibsSameLayout == True:
        # TODO: RESUME HERE: fix case for iteratively growing gibs
        for gibForMask in gibsForMask:  # TODO: test case for deviating number of maskgibs
            uncroppedSearchGibImg = Image.fromarray(np.zeros(newBaseImage.shape, dtype=np.uint8))
            uncroppedSearchGibImg.paste(Image.fromarray(gibForMask['img']), (gibForMask['x'], gibForMask['y']),
                                        Image.fromarray(gibForMask['img']))
            searchGibTransparentMask = np.asarray(uncroppedSearchGibImg)[:, :, 3] == 0
            uncroppedNewGib = deepcopy(newBaseImage)
            uncroppedNewGib[searchGibTransparentMask] = (0, 0, 0, 0)

            newGib = {}
            newGib['id'] = gibForMask['id']
            newGib['x'] = gibForMask['x']
            newGib['y'] = gibForMask['y']
            newGib['img'], center, minX, minY = crop(uncroppedNewGib)
            newGibs.append(newGib)
    return foundGibsSameLayout, newGibs, newShipImageSubfolder
