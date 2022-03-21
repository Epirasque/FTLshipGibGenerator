import random
from copy import copy, deepcopy

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
    originalGibImageArray = deepcopy(gibToPopulate['img'])
    seamCoordinates = deepcopy(gibToPopulate['neighbourToSeam'][neighbourId])
    metalBits = np.zeros(shipImage.shape, dtype=np.uint8)
    tilesToUse = tilesets['default'][LAYER1]
    nrTilesToUse = len(tilesToUse)
    # TODO: use seamCoordinates directly?
    for coordinates in seamCoordinates:
        metalBits[coordinates[0], coordinates[1]] = REMAINING_UNCOVERED_SEAM_PIXEL_COLOR
    # metalBits[np.asarray(seamCoordinates)] = [0, 255, 0, 255]
    seamImageArray = deepcopy(metalBits)
    # TODO: for currentLayer in range(1, 4 + 1): or layer function as variable/parameter, or ...
    nrAttemptsForLayer = 1
    maxNrAttemptsForLayer = NR_MAX_ATTEMPTS_PER_LAYER_TO_POPULATE_SINGLE_SEAM
    remainingUncoveredSeamPixels = np.where(np.all(metalBits == REMAINING_UNCOVERED_SEAM_PIXEL_COLOR, axis=-1))
    while nrAttemptsForLayer < maxNrAttemptsForLayer and np.any(remainingUncoveredSeamPixels):
        nrAttemptsForLayer += 1
        metalBits, remainingUncoveredSeamPixels = attemptTileAttachment(PARAMETERS, gibToPopulate, gibs, gifFrames,
                                                                        metalBits, nrTilesToUse, originalGibImageArray,
                                                                        remainingUncoveredSeamPixels, seamCoordinates,
                                                                        seamImageArray, shipImage, tilesToUse)

    pasteNonTransparentValuesIntoArray(originalGibImageArray, metalBits)
    gibToPopulate['img'] = metalBits


def attemptTileAttachment(PARAMETERS, gibToPopulate, gibs, gifFrames, metalBits, nrTilesToUse, originalGibImageArray,
                          remainingUncoveredSeamPixels, seamCoordinates, seamImageArray, shipImage, tilesToUse):
    isCandidateOriginCoveredByGib = False
    isCandidateValid = False

    attachmentPoint, isDetectionSuccessful, outwardAngle, outwardVectorYX = determineAttachmentPointWithOrientation(
        PARAMETERS, gifFrames, metalBits, originalGibImageArray, remainingUncoveredSeamPixels, seamCoordinates)
    if isDetectionSuccessful == True:
        inwardsSearchX, inwardsSearchY, isCandidateOriginCoveredByGib, tileImageArray, tileOriginCenterPoint = determineCandidateTileWithCoveredOrigin(
            PARAMETERS, attachmentPoint, gifFrames, metalBits, nrTilesToUse, originalGibImageArray, outwardAngle,
            outwardVectorYX, tilesToUse)
    if isCandidateOriginCoveredByGib == True:
        isCandidateValid, metalBitsCandidate, seamPixelsCoveredByCandidate = constructValidCandidate(PARAMETERS,
                                                                                                     attachmentPoint,
                                                                                                     gibToPopulate,
                                                                                                     gibs,
                                                                                                     gifFrames,
                                                                                                     inwardsSearchX,
                                                                                                     inwardsSearchY,
                                                                                                     metalBits,
                                                                                                     originalGibImageArray,
                                                                                                     seamImageArray,
                                                                                                     shipImage,
                                                                                                     tileImageArray,
                                                                                                     tileOriginCenterPoint)
    if isCandidateValid == True:
        metalBits, remainingUncoveredSeamPixels = approveCandidate(PARAMETERS, gifFrames, metalBitsCandidate,
                                                                   originalGibImageArray, remainingUncoveredSeamPixels,
                                                                   seamPixelsCoveredByCandidate)
    remainingUncoveredSeamPixels = updateRemainingSeamPoints(attachmentPoint, metalBits, remainingUncoveredSeamPixels)
    return metalBits, remainingUncoveredSeamPixels


def approveCandidate(PARAMETERS, gifFrames, metalBitsCandidate, originalGibImageArray,
                     remainingUncoveredSeamPixels, seamPixelsCoveredByCandidate):
    metalBits = metalBitsCandidate
    remainingUncoveredSeamPixels = updateRemainingSeamPoints(seamPixelsCoveredByCandidate, metalBits,
                                                             remainingUncoveredSeamPixels)
    animateGibResultAndSeamPreview(PARAMETERS, gifFrames, metalBits, originalGibImageArray,
                                   remainingUncoveredSeamPixels)
    return metalBits, remainingUncoveredSeamPixels


def constructValidCandidate(PARAMETERS, attachmentPoint, gibToPopulate, gibs, gifFrames, inwardsSearchX, inwardsSearchY,
                            metalBits, originalGibImageArray, seamImageArray, shipImage, tileImageArray,
                            tileOriginCenterPoint):
    metalBitsCandidate, seamPixelsCoveredByCandidate = constructMetalBitsCandidateBelowMetalBits(inwardsSearchX,
                                                                                                 inwardsSearchY,
                                                                                                 metalBits,
                                                                                                 seamImageArray,
                                                                                                 tileImageArray,
                                                                                                 tileOriginCenterPoint)
    animateUnverifiedCandidateAttached(PARAMETERS, attachmentPoint, gifFrames, metalBitsCandidate,
                                       originalGibImageArray)
    isCandidateValid = doesCandidateSatisfyConstraints(gibToPopulate, gibs, metalBitsCandidate, shipImage)
    return isCandidateValid, metalBitsCandidate, seamPixelsCoveredByCandidate


def determineCandidateTileWithCoveredOrigin(PARAMETERS, attachmentPoint, gifFrames, metalBits, nrTilesToUse,
                                            originalGibImageArray, outwardAngle, outwardVectorYX, tilesToUse):
    tileImageArray, tileOriginCenterPoint, tileOriginCoordinates = determineTileToAttach(nrTilesToUse, outwardAngle,
                                                                                         tilesToUse)
    alreadyCoveredArea = deepcopy(originalGibImageArray)
    pasteNonTransparentValuesIntoArray(metalBits, alreadyCoveredArea)
    animateAlreadyCoveredArea(PARAMETERS, alreadyCoveredArea, attachmentPoint, gifFrames)
    isCandidateOriginCoveredByGib, inwardsSearchX, inwardsSearchY = searchInwardUntilOriginIsCoveredByGib(PARAMETERS,
                                                                                                          alreadyCoveredArea,
                                                                                                          attachmentPoint,
                                                                                                          gifFrames,
                                                                                                          outwardVectorYX,
                                                                                                          tileOriginCenterPoint,
                                                                                                          tileOriginCoordinates)
    return inwardsSearchX, inwardsSearchY, isCandidateOriginCoveredByGib, tileImageArray, tileOriginCenterPoint


def determineAttachmentPointWithOrientation(PARAMETERS, gifFrames, metalBits, originalGibImageArray,
                                            remainingUncoveredSeamPixels, seamCoordinates):
    attachmentPoint = determineAttachmentPoint(remainingUncoveredSeamPixels)
    isDetectionSuccessful, outwardAngle, outwardVectorYX = determineOutwardDirectionAtPoint(originalGibImageArray,
                                                                                            seamCoordinates,
                                                                                            attachmentPoint,
                                                                                            NEARBY_EDGE_PIXEL_SCAN_RADIUS,
                                                                                            MAXIMUM_SCAN_FOR_TRANSPARENCY_DISTANCE)
    animateAttachmentPointWithOrientation(PARAMETERS, attachmentPoint, gifFrames, isDetectionSuccessful, metalBits,
                                          originalGibImageArray, outwardVectorYX, remainingUncoveredSeamPixels,
                                          seamCoordinates)
    return attachmentPoint, isDetectionSuccessful, outwardAngle, outwardVectorYX


def animateGibResultAndSeamPreview(PARAMETERS, gifFrames, metalBits, originalGibImageArray,
                                   remainingUncoveredSeamPixels):
    if PARAMETERS.ANIMATE_METAL_BITS_FOR_DEVELOPER:
        gifFrame = deepcopy(metalBits)
        pasteNonTransparentValuesIntoArray(originalGibImageArray, gifFrame)
        gifFrames.append(gifFrame)
        gifFrameNextSeamPixels = deepcopy(gifFrame)
        gifFrameNextSeamPixels[remainingUncoveredSeamPixels] = REMAINING_UNCOVERED_SEAM_PIXEL_COLOR
        gifFrames.append(gifFrameNextSeamPixels)


def animateUnverifiedCandidateAttached(PARAMETERS, attachmentPoint, gifFrames, metalBitsCandidate,
                                       originalGibImageArray):
    if PARAMETERS.ANIMATE_METAL_BITS_FOR_DEVELOPER == True:
        gifFrame = deepcopy(originalGibImageArray)
        pasteNonTransparentValuesIntoArray(metalBitsCandidate, gifFrame)
        # TODO: try: gifFrame[np.any(metalBits != [0, 0, 0, 0], axis=-1)] = [0, 0, 255, 255]
        gifFrame[attachmentPoint] = ATTACHMENT_POINT_COLOR
        gifFrames.append(gifFrame)


def constructMetalBitsCandidateBelowMetalBits(inwardsSearchX, inwardsSearchY, metalBits, seamImageArray, tileImageArray,
                                              tileOriginCenterPoint):
    metalBitsCandidate = np.zeros(metalBits.shape, dtype=np.uint8)
    pasteNonTransparentValuesIntoArrayWithOffset(tileImageArray, metalBitsCandidate,
                                                 inwardsSearchY - tileOriginCenterPoint[0],
                                                 inwardsSearchX - tileOriginCenterPoint[1])
    seamPixelsCoveredByCandidate = getVisibleOverlappingPixels(metalBitsCandidate, seamImageArray)
    pasteNonTransparentValuesIntoArray(metalBits, metalBitsCandidate)
    return metalBitsCandidate, seamPixelsCoveredByCandidate


def searchInwardUntilOriginIsCoveredByGib(PARAMETERS, alreadyCoveredArea, attachmentPoint, gifFrames, outwardVectorYX,
                                          tileOriginCenterPoint, tileOriginCoordinates):
    isCandidateOriginCoveredByGib = False
    inwardsOffset = 0
    inwardsSearchY = None
    inwardsSearchX = None
    while inwardsOffset < NR_MAX_DISTANCE_MOVING_TILE_INWARDS and isCandidateOriginCoveredByGib == False:
        inwardsOffset += 1
        inwardsSearchY = round(attachmentPoint[0] - outwardVectorYX[0] * inwardsOffset)
        inwardsSearchX = round(attachmentPoint[1] - outwardVectorYX[1] * inwardsOffset)
        # TODO: use np.where?
        offsetCoordinates = []
        for coordinate in tileOriginCoordinates:
            coordinateY = coordinate[0] + inwardsSearchY - tileOriginCenterPoint[0]
            coordinateX = coordinate[1] + inwardsSearchX - tileOriginCenterPoint[1]
            offsetCoordinates.append((coordinateY, coordinateX))

        if PARAMETERS.ANIMATE_METAL_BITS_FOR_DEVELOPER == True:
            gifFrame = deepcopy(alreadyCoveredArea)
            for offsetCoordinate in offsetCoordinates:
                try:
                    gifFrame[offsetCoordinate[0], offsetCoordinate[1]] = [0, 0, 255, 255]
                except IndexError:
                    pass
            gifFrame[attachmentPoint] = ATTACHMENT_POINT_COLOR
            gifFrames.append(gifFrame)

        isCandidateOriginCoveredByGib = areAllCoordinatesContainedInVisibleArea(offsetCoordinates,
                                                                                alreadyCoveredArea)
    return isCandidateOriginCoveredByGib, inwardsSearchX, inwardsSearchY


def animateAlreadyCoveredArea(PARAMETERS, alreadyCoveredArea, attachmentPoint, gifFrames):
    if PARAMETERS.ANIMATE_METAL_BITS_FOR_DEVELOPER == True:
        gifFrame = deepcopy(alreadyCoveredArea)
        gifFrame[attachmentPoint] = ATTACHMENT_POINT_COLOR
        gifFrames.append(gifFrame)


def determineTileToAttach(nrTilesToUse, outwardAngle, tilesToUse):
    tileId = random.randint(0, nrTilesToUse - 1)
    tileAngleId = (CLOCKWISE_ANGLE_PER_STEP * round(outwardAngle / CLOCKWISE_ANGLE_PER_STEP)) % 360
    tileImageArray = tilesToUse[tileId][tileAngleId]['img']
    tileOriginArea, tileOriginCoordinates, tileOriginCenterPoint = tilesToUse[tileId][tileAngleId]['origin']
    return tileImageArray, tileOriginCenterPoint, tileOriginCoordinates


def updateRemainingSeamPoints(attachmentPoint, metalBits, remainingUncoveredSeamPixels):
    metalBits[attachmentPoint] = BLOCKED_SEAM_PIXELS_COLOR
    remainingUncoveredSeamPixels = np.where(np.all(metalBits == REMAINING_UNCOVERED_SEAM_PIXEL_COLOR, axis=-1))
    return remainingUncoveredSeamPixels


def animateAttachmentPointWithOrientation(PARAMETERS, attachmentPoint, gifFrames, isDetectionSuccessful, metalBits,
                                          originalGibImageArray, outwardVectorYX, remainingUncoveredSeamPixels,
                                          seamCoordinates):
    if PARAMETERS.ANIMATE_METAL_BITS_FOR_DEVELOPER == True:
        gifFrame = deepcopy(metalBits)
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


def determineAttachmentPoint(remainingUncoveredSeamPixels):
    attachmentPointId = random.randint(0, len(remainingUncoveredSeamPixels[0]) - 1)
    attachmentPoint = remainingUncoveredSeamPixels[0][attachmentPointId], remainingUncoveredSeamPixels[1][
        attachmentPointId]
    return attachmentPoint


def doesCandidateSatisfyConstraints(gibToPopulate, gibs, metalBitsCandidate, shipImage):
    isCandidateValid = areAllVisiblePixelsContained(metalBitsCandidate, shipImage)
    if isCandidateValid:
        for otherGib in gibs:
            if gibToPopulate['coversNeighbour'][otherGib['id']] == True:
                if areAnyVisiblePixelsOverlapping(metalBitsCandidate, otherGib['img']) == True:
                    isCandidateValid = False
                    break
    return isCandidateValid
