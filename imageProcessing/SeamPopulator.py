import random

from skimage.draw import line

from fileHandling.MetalBitsLoader import LAYER1, CLOCKWISE_ANGLE_PER_STEP
from imageProcessing.GibTopologizer import *
from imageProcessing.ImageProcessingUtilities import *
from imageProcessing.MetalBitsConstants import *


def populateSeams(gibs, shipImage, tilesets, gifFrames, PARAMETERS):
    for gibToPopulate in gibs:
        for neighbouringGib in gibs:
            neighbourId = neighbouringGib['id']
            if gibToPopulate['id'] != neighbourId:
                if gibToPopulate['coveredByNeighbour'][neighbourId] == True:
                    populateSeam(gibToPopulate, gibs, neighbourId, shipImage, tilesets, gifFrames, PARAMETERS)


def populateSeam(gibToPopulate, gibs, neighbourId, shipImage, tilesets, gifFrames, PARAMETERS):
    originalGibImageArray = copy(gibToPopulate['img'])
    seamCoordinates = copy(gibToPopulate['neighbourToSeam'][neighbourId])
    metalBits = np.zeros(shipImage.shape, dtype=np.uint8)
    tilesToUse = tilesets['default'][LAYER1]
    nrTilesToUse = len(tilesToUse)
    # TODO: use seamCoordinates directly?
    for coordinates in seamCoordinates:
        metalBits[coordinates[0], coordinates[1]] = REMAINING_UNCOVERED_SEAM_PIXEL_COLOR
    # metalBits[np.asarray(seamCoordinates)] = [0, 255, 0, 255]
    seamImageArray = copy(metalBits)
    # TODO: for currentLayer in range(1, 4 + 1): or layer function as variable/parameter, or ...
    nrAttemptsForLayer = 1
    maxNrAttemptsForLayer = NR_MAX_ATTEMPTS_PER_LAYER_TO_POPULATE_SINGLE_SEAM
    remainingUncoveredSeamPixels = np.where(np.all(metalBits == REMAINING_UNCOVERED_SEAM_PIXEL_COLOR, axis=-1))
    while nrAttemptsForLayer < maxNrAttemptsForLayer and np.any(remainingUncoveredSeamPixels):
        nrAttemptsForLayer += 1

        attachmentPointId = random.randint(0, len(remainingUncoveredSeamPixels[0]) - 1)
        attachmentPoint = remainingUncoveredSeamPixels[0][attachmentPointId], remainingUncoveredSeamPixels[1][
            attachmentPointId]

        isDetectionSuccessful, outwardAngle, outwardVectorYX = determineOutwardDirectionAtPoint(originalGibImageArray,
                                                                                                seamCoordinates,
                                                                                                attachmentPoint,
                                                                                                NEARBY_EDGE_PIXEL_SCAN_RADIUS,
                                                                                                MAXIMUM_SCAN_FOR_TRANSPARENCY_DISTANCE)
        if PARAMETERS.ANIMATE_METAL_BITS_FOR_DEVELOPER == True:
            gifFrame = copy(metalBits)
            pasteNonTransparentValuesIntoArray(originalGibImageArray, gifFrame)
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
            gifFrame[attachmentPoint] = ATTACHMENT_POINT_COLOR
            gifFrames.append(gifFrame)

        if isDetectionSuccessful == False:
            metalBits[attachmentPoint] = BLOCKED_SEAM_PIXELS_COLOR
            remainingUncoveredSeamPixels = np.where(np.all(metalBits == REMAINING_UNCOVERED_SEAM_PIXEL_COLOR, axis=-1))
            continue

        tileId = random.randint(0, nrTilesToUse - 1)
        tileAngleId = (CLOCKWISE_ANGLE_PER_STEP * round(outwardAngle / CLOCKWISE_ANGLE_PER_STEP)) % 360
        tileImageArray = tilesToUse[tileId][tileAngleId]['img']
        tileOriginArea, tileOriginCoordinates, tileOriginCenterPoint = tilesToUse[tileId][tileAngleId]['origin']

        alreadyCoveredArea = copy(originalGibImageArray)
        pasteNonTransparentValuesIntoArray(metalBits, alreadyCoveredArea)

        if PARAMETERS.ANIMATE_METAL_BITS_FOR_DEVELOPER == True:
            gifFrame = copy(alreadyCoveredArea)
            gifFrame[attachmentPoint] = ATTACHMENT_POINT_COLOR
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

            if PARAMETERS.ANIMATE_METAL_BITS_FOR_DEVELOPER == True:
                gifFrame = copy(alreadyCoveredArea)
                for offsetCoordinate in offsetCoordinates:
                    try:
                        gifFrame[offsetCoordinate[0], offsetCoordinate[1]] = [0, 0, 255, 255]
                    except IndexError:
                        pass
                gifFrame[attachmentPoint] = ATTACHMENT_POINT_COLOR
                gifFrames.append(gifFrame)

            isCandidateOriginCoveredByGib = areAllCoordinatesContainedInVisibleArea(offsetCoordinates,
                                                                                    alreadyCoveredArea)
        if isCandidateOriginCoveredByGib == False:
            metalBits[attachmentPoint] = BLOCKED_SEAM_PIXELS_COLOR
            remainingUncoveredSeamPixels = np.where(np.all(metalBits == REMAINING_UNCOVERED_SEAM_PIXEL_COLOR, axis=-1))
            continue

        metalBitsCandidate = np.zeros(metalBits.shape, dtype=np.uint8)
        pasteNonTransparentValuesIntoArrayWithOffset(tileImageArray, metalBitsCandidate,
                                                     inwardsSearchY - tileOriginCenterPoint[0],
                                                     inwardsSearchX - tileOriginCenterPoint[1])
        seamPixelsCoveredByCandidate = getVisibleOverlappingPixels(metalBitsCandidate, seamImageArray)
        pasteNonTransparentValuesIntoArray(metalBits, metalBitsCandidate)

        if PARAMETERS.ANIMATE_METAL_BITS_FOR_DEVELOPER == True:
            gifFrame = copy(originalGibImageArray)
            pasteNonTransparentValuesIntoArray(metalBitsCandidate, gifFrame)
            # TODO: try: gifFrame[np.any(metalBits != [0, 0, 0, 0], axis=-1)] = [0, 0, 255, 255]
            gifFrame[attachmentPoint] = ATTACHMENT_POINT_COLOR
            gifFrames.append(gifFrame)

        isCandidateValid = doesCandidateSatisfyConstraints(gibToPopulate, gibs, metalBitsCandidate, shipImage)
        if isCandidateValid == False:
            metalBits[attachmentPoint] = BLOCKED_SEAM_PIXELS_COLOR
            remainingUncoveredSeamPixels = np.where(np.all(metalBits == REMAINING_UNCOVERED_SEAM_PIXEL_COLOR, axis=-1))
            continue

        metalBits = metalBitsCandidate
        metalBits[seamPixelsCoveredByCandidate] = BLOCKED_SEAM_PIXELS_COLOR
        remainingUncoveredSeamPixels = np.where(np.all(metalBits == REMAINING_UNCOVERED_SEAM_PIXEL_COLOR, axis=-1))
        if PARAMETERS.ANIMATE_METAL_BITS_FOR_DEVELOPER:
            gifFrame = copy(metalBits)
            pasteNonTransparentValuesIntoArray(originalGibImageArray, gifFrame)
            gifFrames.append(gifFrame)
            gifFrameNextSeamPixels = copy(gifFrame)
            gifFrameNextSeamPixels[remainingUncoveredSeamPixels] = REMAINING_UNCOVERED_SEAM_PIXEL_COLOR
            gifFrames.append(gifFrameNextSeamPixels)

    pasteNonTransparentValuesIntoArray(originalGibImageArray, metalBits)
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
