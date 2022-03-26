from copy import deepcopy

import numpy as np

from imageProcessing.ImageProcessingUtilities import pasteNonTransparentValuesIntoArray, getDistanceBetweenPoints
from imageProcessing.MetalBitsConstants import SEAM_DETECTION_SEARCH_RADIUS


def buildSeamTopology(gibs, shipImage):
    nrGibs = len(gibs)
    currentZ = 1
    for gib in gibs:
        # overwrite fallback defined by non-metalbit part of segmenter
        gib['z'] = None
    centerMostGib = getCenterMostGib(gibs, shipImage)
    buildSeamTopologyForGib(centerMostGib, currentZ, gibs, nrGibs, shipImage)

    for currentZ in range(2, nrGibs + 1):
        for gib in gibs:
            if gib['z'] == None:
                nextGib = gib
                break
        buildSeamTopologyForGib(nextGib, currentZ, gibs, nrGibs, shipImage)


def orderGibsByZCoordinates(gibs):
    newGibs = []
    nextId = 1
    newIdsToOldIds = {}
    # TODO: also adjust neighbour-ids!
    for z in range(len(gibs), 0, -1):
        for gib in gibs:
            if gib['z'] == z:
                newIdsToOldIds[nextId] = deepcopy(gib['id'])
                gib['id'] = nextId
                nextId += 1
                newGibs.append(deepcopy(gib))
                break
    for newGib in newGibs:
        coveredByNeighhbourWithOldIds = deepcopy(newGib['coveredByNeighbour'])
        coversNeighhbourWithOldIds = deepcopy(newGib['coversNeighbour'])
        neighbourToSeamWithOldIds = deepcopy(newGib['neighbourToSeam'])
        newGib['coveredByNeighbour'] = {}
        newGib['coversNeighbour'] = {}
        newGib['neighbourToSeam'] = {}
        for newNeighbourGib in newGibs:
            newNeighbourId = newNeighbourGib['id']
            oldNeighbourId = newIdsToOldIds[newNeighbourId]
            newGib['coveredByNeighbour'][newNeighbourId] = coveredByNeighhbourWithOldIds[oldNeighbourId]
            newGib['coversNeighbour'][newNeighbourId] = coversNeighhbourWithOldIds[oldNeighbourId]
            newGib['neighbourToSeam'][newNeighbourId] = neighbourToSeamWithOldIds[oldNeighbourId]

    return newGibs


def animateTopology(gifImages, PARAMETERS, gibs):
    if PARAMETERS.ANIMATE_METAL_BITS_FOR_DEVELOPER == True:
        gibImageArray = np.zeros(gibs[0]['img'].shape, dtype=np.uint8)
        # here: decreasing z-values
        for gibToShow in gibs:
            pasteNonTransparentValuesIntoArray(gibToShow['img'], gibImageArray)
            for neighbouringGib in gibs:
                neighbourId = neighbouringGib['id']
                if gibToShow['id'] != neighbourId:
                    if gibToShow['coveredByNeighbour'][neighbourId] == True:
                        seamCoordinates = gibToShow['neighbourToSeam'][neighbourId]
                        for seamPoint in seamCoordinates:
                            y, x = seamPoint
                            gibImageArray[y, x] = [0, 255, 0, 255]
                    if gibToShow['coversNeighbour'][neighbourId] == True:
                        seamCoordinates = gibToShow['neighbourToSeam'][neighbourId]
                        for seamPoint in seamCoordinates:
                            y, x = seamPoint
                            gibImageArray[y, x] = [255, 0, 0, 255]
            gifImages.append(np.ma.copy(gibImageArray))


def buildSeamTopologyForGib(gibToProcess, currentZ, gibs, nrGibs, shipImage):
    initializeGibAttributes(currentZ, gibToProcess, nrGibs)
    determineSeamsWithNeighbours(gibToProcess, gibs, shipImage)
    defineTopologyWithNeighbours(gibToProcess, gibs)


def initializeGibAttributes(currentZ, gibToProcess, nrGibs):
    gibToProcess['z'] = currentZ
    gibToProcess['coversNeighbour'] = {}
    gibToProcess['coveredByNeighbour'] = {}
    gibToProcess['neighbourToSeam'] = {}
    for gibId in range(1, nrGibs + 1):
        # if gibId != gibToProcess['id']: <- requires none check, not needed
        gibToProcess['neighbourToSeam'][gibId] = []
        gibToProcess['coversNeighbour'][gibId] = False
        gibToProcess['coveredByNeighbour'][gibId] = False


def determineSeamsWithNeighbours(gibToProcess, gibs, shipImage):
    gibImageArray = gibToProcess['img']
    # TODO: refactor into something more efficient to improve performance
    for x in range(gibImageArray.shape[1]):
        for y in range(gibImageArray.shape[0]):
            if gibImageArray[y, x, 3] == 255:
                for xSearchOffset in range(-SEAM_DETECTION_SEARCH_RADIUS, SEAM_DETECTION_SEARCH_RADIUS + 1):
                    xSearch = x + xSearchOffset
                    for ySearchOffset in range(-SEAM_DETECTION_SEARCH_RADIUS, SEAM_DETECTION_SEARCH_RADIUS + 1):
                        ySearch = y + ySearchOffset
                        try:
                            if gibImageArray[ySearch, xSearch, 3] < 255:
                                if shipImage[ySearch, xSearch, 3] == 255:
                                    for gibNeighbour in gibs:
                                        if gibNeighbour['id'] != gibToProcess['id']:
                                            if gibNeighbour['img'][ySearch, xSearch, 3] == 255:
                                                gibToProcess['neighbourToSeam'][gibNeighbour['id']].append(
                                                    (y, x))
                        except:
                            pass
    for neighbourId in gibToProcess['neighbourToSeam']:
        gibToProcess['neighbourToSeam'][neighbourId] = [tuple(row) for row in
                                                        np.unique(gibToProcess['neighbourToSeam'][neighbourId], axis=0)]


def defineTopologyWithNeighbours(gibToProcess, gibs):
    for neighbouringGib in gibs:
        neighbourId = neighbouringGib['id']
        if neighbourId != gibToProcess['id']:
            if len(gibToProcess['neighbourToSeam'][neighbourId]) > 0:
                if neighbouringGib['z'] != None:  # this implies the z is smaller than current gib
                    gibToProcess['coversNeighbour'][neighbourId] = True
                    gibToProcess['coveredByNeighbour'][neighbourId] = False
                else:
                    gibToProcess['coversNeighbour'][neighbourId] = False
                    gibToProcess['coveredByNeighbour'][neighbourId] = True


def getCenterMostGib(gibs, shipImage):
    shipCenter = shipImage.shape[0] / 2, shipImage.shape[1] / 2
    centerMostGib = gibs[0]
    upperBound = shipCenter[0] * shipCenter[1]
    closestDistanceToCenter = upperBound
    for gib in gibs:
        distanceToCenter = getDistanceBetweenPoints(gib['center']['x'], gib['center']['y'], shipCenter[1],
                                                    shipCenter[0])
        if distanceToCenter < closestDistanceToCenter:
            centerMostGib = gib
    return centerMostGib
