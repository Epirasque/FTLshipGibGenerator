from pickletools import optimize

import numpy as np
from PIL import Image
from imageio import get_writer

from imageProcessing.ImageAnalyser import getDistanceBetweenPoints
from imageProcessing.ImageCropper import cropImage


def attachMetalBits(gibs, shipImage, tilesets, parameters, shipImageName):
    gifFrames = initialGifImageArray(parameters, shipImage)
    uncropGibs(gibs, shipImage)
    buildSeamTopology(gibs, shipImage, gifFrames, parameters)
    populateSeams(gibs, shipImage, tilesets)
    orderGibsByZCoordinates(gibs)
    cropAndUpdateGibs(gibs)
    saveGif(gifFrames, shipImageName, parameters)
    return gibs


def saveGif(gifFrames, shipImageName, parameters):
    if parameters.ANIMATE_METAL_BITS_FOR_DEVELOPER == True:
        filePath = '../metalBitsDebugAnimations/%s.gif' % shipImageName
        # TODO: delete it first to avoid gifs with multiple loops?
        with get_writer(filePath, mode='I') as writer:
            for gifFrame in gifFrames:
                writer.append_data(gifFrame)
        optimize(filePath)


def initialGifImageArray(parameters, shipImage):
    gifFrames = []
    if parameters.ANIMATE_METAL_BITS_FOR_DEVELOPER == True:
        gifFrames.append(np.asarray(shipImage))
    return gifFrames


def populateSeams(gibs, shipImage, tilesets):
    for gibToPopulate in gibs:
        for neighbouringGib in gibs:
            neighbourId = neighbouringGib['id']
            if gibToPopulate['id'] != neighbourId:
                if gibToPopulate['coveredByNeighbour'][neighbourId] == True:
                    populateSeam(gibToPopulate, shipImage, tilesets)


def populateSeam(gibToPopulate, shipImage, tilesets):
    # TODO: ensure does not reach into any of coversNeighbour or outside of ship image shape -> use mask, also one for gib itself
    pass


def buildSeamTopology(gibs, shipImage, gifImages, parameters):
    nrGibs = len(gibs)
    currentZ = 1
    for gib in gibs:
        # overwrite fallback defined by non-metalbit part of segmenter
        gib['z'] = None
    centerMostGib = getCenterMostGib(gibs, shipImage)
    buildSeamTopologyForGib(centerMostGib, currentZ, gibs, nrGibs, shipImage, gifImages, parameters)

    for currentZ in range(2, nrGibs + 1):
        for gib in gibs:
            if gib['z'] == None:
                nextGib = gib
                break
        buildSeamTopologyForGib(nextGib, currentZ, gibs, nrGibs, shipImage, gifImages, parameters)


def orderGibsByZCoordinates(gibs):
    gibs.reverse()


def animateTopology(gibToProcess, gifImages, parameters):
    if parameters.ANIMATE_METAL_BITS_FOR_DEVELOPER == True:
        gifImages.append(gibToProcess['img'])
        # TODO: more...


def buildSeamTopologyForGib(gibToProcess, currentZ, gibs, nrGibs, shipImage, gifImages, parameters):
    initializeGibAttributes(currentZ, gibToProcess, nrGibs)
    determineSeamsWithNeighbours(gibToProcess, gibs, shipImage)
    defineTopologyWithNeighbours(gibToProcess, gibs, nrGibs)
    animateTopology(gibToProcess, gifImages, parameters)


def defineTopologyWithNeighbours(gibToProcess, gibs, nrGibs):
    for neighbourId in range(1, nrGibs + 1):
        if neighbourId != gibToProcess['id']:
            if len(gibToProcess['neighbourToSeam'][neighbourId]) > 0:
                if gibs[neighbourId]['z'] != None:  # this implies the z is smaller than current gib
                    gibToProcess['coversNeighbour'][neighbourId] = True
                    gibToProcess['coveredByNeighbour'][neighbourId] = False
                else:
                    gibToProcess['coversNeighbour'][neighbourId] = False
                    gibToProcess['coveredByNeighbour'][neighbourId] = True


def determineSeamsWithNeighbours(gibToProcess, gibs, shipImage):
    searchRadius = 1
    gibImageArray = gibToProcess['img']
    # TODO: refactor into something more efficient to improve performance
    for x in range(gibImageArray.shape[1]):
        for y in range(gibImageArray.shape[0]):
            if gibImageArray[y, x, 3] != 0:
                for xSearchOffset in range(-searchRadius, searchRadius + 1):
                    xSearch = x + xSearchOffset
                    for ySearchOffset in range(-searchRadius, searchRadius + 1):
                        ySearch = y + ySearchOffset
                        try:
                            if gibImageArray[ySearch, xSearch, 3] == 0:
                                if shipImage[ySearch, xSearch, 3] != 0:
                                    for gibNeighbour in gibs:
                                        if gibNeighbour['id'] != gibImageArray['id']:
                                            if gibNeighbour['img'][ySearch, xSearch, 3] != 0:
                                                gibToProcess['neighbourToSeam'].append([ySearch, xSearch])
                        except:
                            pass


def initializeGibAttributes(currentZ, gibToProcess, nrGibs):
    gibToProcess['z'] = currentZ
    gibToProcess['coversNeighbour'] = {}
    gibToProcess['coveredByNeighbour'] = {}
    gibToProcess['neighbourToSeam'] = {}
    for gibId in range(1, nrGibs + 1):
        if gibId != gibToProcess['id']:
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
