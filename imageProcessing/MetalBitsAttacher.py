import os
import random

import imageio
import numpy as np
from PIL import Image
from numpy.ma import copy

from imageProcessing.ImageCropper import cropImage
from imageProcessing.ImageProcessingUtilities import getDistanceBetweenPoints, areAllVisiblePixelsContained, \
    areVisiblePixelsOverlapping, pasteNonTransparentBlackValuesIntoArray

NR_MAX_ATTEMPTS_PER_LAYER_TO_POPULATE_SINGLE_SEAM = 20
EDGE_SEARCH_RADIUS = 1


def attachMetalBits(gibs, shipImage, tilesets, parameters, shipImageName):
    gifFrames = initialGifImageArray(parameters, shipImage)
    uncropGibs(gibs, shipImage)
    buildSeamTopology(gibs, shipImage)
    gibs = orderGibsByZCoordinates(gibs)
    animateTopology(gifFrames, parameters, gibs)
    populateSeams(gibs, shipImage, tilesets, gifFrames, parameters)
    cropAndUpdateGibs(gibs)
    saveGif(gifFrames, shipImageName, parameters)
    return gibs


def saveGif(gifFrames, shipImageName, parameters):
    if parameters.ANIMATE_METAL_BITS_FOR_DEVELOPER == True:
        filePath = '../metalBitsDebugAnimations/%s.gif' % shipImageName
        if os.path.exists(filePath):
            os.remove(filePath)
        imageio.mimwrite(filePath, gifFrames, format='GIF', fps=2.)
        # TODO: smaller filesize using pygifsicle.optimize(filePath)


def initialGifImageArray(parameters, shipImage):
    gifFrames = []
    if parameters.ANIMATE_METAL_BITS_FOR_DEVELOPER == True:
        gifFrames.append(np.asarray(shipImage, dtype=np.uint8))
    return gifFrames


def populateSeams(gibs, shipImage, tilesets, gifFrames, parameters):
    for gibToPopulate in gibs:
        for neighbouringGib in gibs:
            neighbourId = neighbouringGib['id']
            if gibToPopulate['id'] != neighbourId:
                if gibToPopulate['coveredByNeighbour'][neighbourId] == True:
                    populateSeam(gibToPopulate, gibs, neighbourId, shipImage, tilesets, gifFrames, parameters)


def populateSeam(gibToPopulate, gibs, neighbourId, shipImage, tilesets, gifFrames, parameters):
    # TODO: ensure does not reach into any of coversNeighbour or outside of ship image shape -> use mask, also one for gib itself
    seamCoordinates = gibToPopulate['neighbourToSeam'][neighbourId]
    metalBits = np.zeros(shipImage.shape, dtype=np.uint8)

    for coordinates in seamCoordinates:
        metalBits[coordinates] = [0, 255, 0, 255]
    # metalBits[np.asarray(seamCoordinates)] = [0, 255, 0, 255]
    # TODO: for currentLayer in range(1, 4 + 1): or layer function as variable/parameter, or ...
    nrAttemptsForLayer = 1
    maxNrAttemptsForLayer = NR_MAX_ATTEMPTS_PER_LAYER_TO_POPULATE_SINGLE_SEAM
    remainingUncoveredSeamPixels = np.where(np.all(metalBits == [0, 255, 0, 255], axis=-1))
    while nrAttemptsForLayer < maxNrAttemptsForLayer and np.any(remainingUncoveredSeamPixels):
        nrAttemptsForLayer += 1
        metalBitsCandidate = copy(metalBits)

        # TODO: properly add to metal bits using tilesets
        randomPixelId = random.randint(0, len(remainingUncoveredSeamPixels[0]) - 1)
        randomPixel = remainingUncoveredSeamPixels[0][randomPixelId], remainingUncoveredSeamPixels[1][randomPixelId]
        metalBitsCandidate[randomPixel] = [63, 0, 255, 255]

        isCandidateValid = doesCandidateSatisfyConstraints(gibToPopulate, gibs, metalBitsCandidate, shipImage)
        if isCandidateValid == True:
            metalBits = metalBitsCandidate
            if parameters.ANIMATE_METAL_BITS_FOR_DEVELOPER:
                gifFrame = copy(gibToPopulate['img'])
                pasteNonTransparentBlackValuesIntoArray(metalBits, gifFrame)
                gifFrames.append(gifFrame)
        remainingUncoveredSeamPixels = np.where(np.all(metalBits == [0, 255, 0, 255], axis=-1))

    pasteNonTransparentBlackValuesIntoArray(gibToPopulate['img'], metalBits)
    gibToPopulate['img'] = metalBits


def doesCandidateSatisfyConstraints(gibToPopulate, gibs, metalBitsCandidate, shipImage):
    isCandidateValid = areAllVisiblePixelsContained(metalBitsCandidate, shipImage)
    if isCandidateValid:
        for otherGib in gibs:
            if gibToPopulate['coversNeighbour'][otherGib['id']] == True:
                if areVisiblePixelsOverlapping(metalBitsCandidate, otherGib['img']) == True:
                    isCandidateValid = False
                    break
    return isCandidateValid


def animateTopology(gifImages, parameters, gibs):
    if parameters.ANIMATE_METAL_BITS_FOR_DEVELOPER == True:
        gibImageArray = np.zeros(gibs[0]['img'].shape, dtype=np.uint8)
        # here: decreasing z-values
        for gibToShow in gibs:
            pasteNonTransparentBlackValuesIntoArray(gibToShow['img'], gibImageArray)
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
            gifImages.append(copy(gibImageArray))


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
    for z in range(len(gibs), 0, -1):
        for gib in gibs:
            if gib['z'] == z:
                gib['id'] = nextId
                nextId += 1
                newGibs.append(gib)
                break
    return newGibs


def buildSeamTopologyForGib(gibToProcess, currentZ, gibs, nrGibs, shipImage):
    initializeGibAttributes(currentZ, gibToProcess, nrGibs)
    determineSeamsWithNeighbours(gibToProcess, gibs, shipImage)
    defineTopologyWithNeighbours(gibToProcess, gibs)


def determineSeamsWithNeighbours(gibToProcess, gibs, shipImage):
    gibImageArray = gibToProcess['img']
    # TODO: refactor into something more efficient to improve performance
    for x in range(gibImageArray.shape[1]):
        for y in range(gibImageArray.shape[0]):
            if gibImageArray[y, x, 3] == 255:
                for xSearchOffset in range(-EDGE_SEARCH_RADIUS, EDGE_SEARCH_RADIUS + 1):
                    xSearch = x + xSearchOffset
                    for ySearchOffset in range(-EDGE_SEARCH_RADIUS, EDGE_SEARCH_RADIUS + 1):
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


def cropAndUpdateGibs(gibs):
    for gib in gibs:
        croppedGibArray, center, minX, minY = cropImage(gib['img'])
        # TODO: reenable, but its slow nrVisiblePixels = sum(matchingSegmentIndex.flatten() == True)

        gib['img'] = croppedGibArray
        gib['center'] = center
        gib['x'] = minX
        gib['y'] = minY
        oldMass = gib['mass']
        newMass = (center['x'] - minX) * (center['y'] - minY) * 4  # TODO: reenable nrVisiblePixels
        # assume metal bits only have half of the mass as normal gib pixels
        gib['mass'] = round((newMass + oldMass) / 2)


def uncropGibs(gibs, shipImage):
    for gib in gibs:
        croppedGib = Image.fromarray(gib['img'])
        uncroppedGib = Image.fromarray(np.zeros(shipImage.shape, dtype=np.uint8))
        uncroppedGib.paste(croppedGib, (gib['x'], gib['y']), croppedGib)
        gib['img'] = np.asarray(uncroppedGib)


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
