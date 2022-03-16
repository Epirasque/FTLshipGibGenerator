import os
import random

import imageio
import numpy as np
from PIL import Image
from numpy.ma import copy
from skimage.draw import line

from fileHandling.MetalBitsLoader import LAYER1, CLOCKWISE_ANGLE_PER_STEP
from imageProcessing.ImageCropper import cropImage
from imageProcessing.ImageProcessingUtilities import getDistanceBetweenPoints, areAllVisiblePixelsContained, \
    areAnyVisiblePixelsOverlapping, pasteNonTransparentValuesIntoArray, determineOutwardDirectionAtPoint, \
    areAllCoordinatesContainedInVisibleArea, findEdgePixelsInSearchRadius, pasteNonTransparentValuesIntoArrayWithOffset

REMAINING_UNCOVERED_SEAM_PIXEL_COLOR = [253, 254, 255, 255]

NR_MAX_ATTEMPTS_PER_LAYER_TO_POPULATE_SINGLE_SEAM = 20 #50
NR_MAX_DISTANCE_MOVING_TILE_INWARDS = 5 #20
SEAM_DETECTION_SEARCH_RADIUS = 1
NEARBY_EDGE_PIXEL_SCAN_RADIUS = 8  # 8
SCAN_FOR_TRANSPARENCY_DISTANCE = 2  # 2


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
        imageio.mimwrite(filePath, gifFrames, format='GIF', fps=5.)
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
    originalGibImage = copy(gibToPopulate['img'])
    seamCoordinates = copy(gibToPopulate['neighbourToSeam'][neighbourId])
    metalBits = np.zeros(shipImage.shape, dtype=np.uint8)
    tilesToUse = tilesets['default'][LAYER1]
    nrTilesToUse = len(tilesToUse)
    # TODO: use seamCoordinates directly?
    for coordinates in seamCoordinates:
        metalBits[coordinates[0], coordinates[1]] = REMAINING_UNCOVERED_SEAM_PIXEL_COLOR

    # metalBits[np.asarray(seamCoordinates)] = [0, 255, 0, 255]
    # TODO: for currentLayer in range(1, 4 + 1): or layer function as variable/parameter, or ...
    nrAttemptsForLayer = 1
    maxNrAttemptsForLayer = NR_MAX_ATTEMPTS_PER_LAYER_TO_POPULATE_SINGLE_SEAM
    remainingUncoveredSeamPixels = np.where(np.all(metalBits == REMAINING_UNCOVERED_SEAM_PIXEL_COLOR, axis=-1))
    while nrAttemptsForLayer < maxNrAttemptsForLayer and np.any(remainingUncoveredSeamPixels):
        nrAttemptsForLayer += 1

        # TODO: properly add to metal bits using tilesets
        attachmentPointId = random.randint(0, len(remainingUncoveredSeamPixels[0]) - 1)
        attachmentPoint = remainingUncoveredSeamPixels[0][attachmentPointId], remainingUncoveredSeamPixels[1][
            attachmentPointId]

        # TODO: include in debug animation, similar to prototype
        isDetectionSuccessful, outwardAngle, outwardVectorYX = determineOutwardDirectionAtPoint(originalGibImage,
                                                                                                seamCoordinates,
                                                                                                attachmentPoint,
                                                                                                NEARBY_EDGE_PIXEL_SCAN_RADIUS,
                                                                                                SCAN_FOR_TRANSPARENCY_DISTANCE)
        if parameters.ANIMATE_METAL_BITS_FOR_DEVELOPER == True:
            gifFrame = copy(metalBits)
            pasteNonTransparentValuesIntoArray(originalGibImage, gifFrame)
            edgeCoordinatesInRadiusY, edgeCoordinatesInRadiusX = findEdgePixelsInSearchRadius(seamCoordinates,
                                                                                              attachmentPoint,
                                                                                              NEARBY_EDGE_PIXEL_SCAN_RADIUS)
            # TODO: only one needed
            # for coordinates in seamCoordinates:
            #    gifFrame[coordinates[0], coordinates[1]] = [63, 63, 63, 255]
            gifFrame[remainingUncoveredSeamPixels] = REMAINING_UNCOVERED_SEAM_PIXEL_COLOR
            gifFrame[edgeCoordinatesInRadiusY, edgeCoordinatesInRadiusX] = [255, 0, 0, 255]

            lineY_A, lineX_A = line(attachmentPoint[0], attachmentPoint[1],
                                    attachmentPoint[0] + round(outwardVectorYX[0] * 50),
                                    attachmentPoint[1] + round(outwardVectorYX[1] * 50))
            # TODO avoid out of bounds (workaround: uncropped gib which is fine; should be basis later on anyway)
            if isDetectionSuccessful == True:
                gifFrame[lineY_A, lineX_A] = [0, 127, 255, 255]
            else:
                gifFrame[lineY_A, lineX_A] = [255, 127, 0, 255]
            gifFrames.append(gifFrame)

        if isDetectionSuccessful == False:
            continue

        tileId = random.randint(0, nrTilesToUse - 1)
        tileAngleId = (CLOCKWISE_ANGLE_PER_STEP * round(outwardAngle / CLOCKWISE_ANGLE_PER_STEP)) % 360
        tileImageArray = tilesToUse[tileId][tileAngleId]['img']
        tileOriginArea, tileOriginCoordinates, tileOriginCenterPoint = tilesToUse[tileId][tileAngleId]['origin']

        alreadyCoveredArea = copy(originalGibImage)
        pasteNonTransparentValuesIntoArray(metalBits, alreadyCoveredArea)

        if parameters.ANIMATE_METAL_BITS_FOR_DEVELOPER == True:
            gifFrame = copy(alreadyCoveredArea)
            gifFrames.append(gifFrame)

        isCandidateOriginCoveredByGib = False
        inwardsOffset = 0
        inwardsSearchY = None
        inwardsSearchX = None
        while inwardsOffset < NR_MAX_DISTANCE_MOVING_TILE_INWARDS and isCandidateOriginCoveredByGib == False:
            inwardsOffset += 1
            inwardsSearchY = round(attachmentPoint[0] - outwardVectorYX[0] * inwardsOffset)
            inwardsSearchX = round(attachmentPoint[1] - outwardVectorYX[1] * inwardsOffset)
            # TODO: use np.where?
            offsetCoordinates = copy(tileOriginCoordinates)
            for coordinate in offsetCoordinates:
                coordinate[0] += inwardsSearchY - tileOriginCenterPoint[0]
                coordinate[1] += inwardsSearchX - tileOriginCenterPoint[1]

            if parameters.ANIMATE_METAL_BITS_FOR_DEVELOPER == True:
                gifFrame = copy(alreadyCoveredArea)
                for offsetCoordinate in offsetCoordinates:
                    try:
                        gifFrame[offsetCoordinate[0], offsetCoordinate[1]] = [0, 0, 255, 255]
                    except IndexError:
                        pass
                gifFrames.append(gifFrame)

            isCandidateOriginCoveredByGib = areAllCoordinatesContainedInVisibleArea(offsetCoordinates,
                                                                                    alreadyCoveredArea)
        if isCandidateOriginCoveredByGib == False:
            continue

        metalBitsCandidate = copy(metalBits)
        pasteNonTransparentValuesIntoArrayWithOffset(tileImageArray, metalBitsCandidate,
                                                     inwardsSearchY - tileOriginCenterPoint[0],
                                                     inwardsSearchX - tileOriginCenterPoint[1])

        if parameters.ANIMATE_METAL_BITS_FOR_DEVELOPER == True:
            gifFrame = copy(originalGibImage)
            pasteNonTransparentValuesIntoArray(metalBitsCandidate, gifFrame)
            # TODO: try: gifFrame[np.any(metalBits != [0, 0, 0, 0], axis=-1)] = [0, 0, 255, 255]
            gifFrames.append(gifFrame)

        isCandidateValid = doesCandidateSatisfyConstraints(gibToPopulate, gibs, metalBitsCandidate, shipImage)
        if isCandidateValid == False:
            continue

        metalBits = metalBitsCandidate
        remainingUncoveredSeamPixels = np.where(np.all(metalBits == REMAINING_UNCOVERED_SEAM_PIXEL_COLOR, axis=-1))
        if parameters.ANIMATE_METAL_BITS_FOR_DEVELOPER:
            gifFrame = copy(metalBits)
            pasteNonTransparentValuesIntoArray(originalGibImage, gifFrame)
            gifFrames.append(gifFrame)
            gifFrameNextSeamPixels = copy(gifFrame)
            gifFrameNextSeamPixels[remainingUncoveredSeamPixels] = REMAINING_UNCOVERED_SEAM_PIXEL_COLOR
            gifFrames.append(gifFrameNextSeamPixels)

    pasteNonTransparentValuesIntoArray(originalGibImage, metalBits)
    gibToPopulate['img'] = metalBits


def doesCandidateSatisfyConstraints(gibToPopulate, gibs, metalBitsCandidate, shipImage):
    isCandidateValid = areAllVisiblePixelsContained(metalBitsCandidate, shipImage)
    if isCandidateValid:
        for otherGib in gibs:
            if gibToPopulate['coversNeighbour'][otherGib['id']] == True:
                if areAnyVisiblePixelsOverlapping(metalBitsCandidate, otherGib['img']) == True:
                    isCandidateValid = False
                    break
    return isCandidateValid


def animateTopology(gifImages, parameters, gibs):
    if parameters.ANIMATE_METAL_BITS_FOR_DEVELOPER == True:
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
