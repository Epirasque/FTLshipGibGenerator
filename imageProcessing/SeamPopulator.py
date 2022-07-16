import random

from skimage.draw import line

from fileHandling.MetalBitsLoader import LAYER1
from flow.GeneratorLooper import logHighestMemoryUsage
from flow.MemoryManagement import cleanUpMemory
from imageProcessing.DebugAnimator import saveGif
from imageProcessing.ImageProcessingUtilities import *
from imageProcessing.MetalBitsConstants import *


def populateSeams(gibs, shipImageName, shipImage, tilesets, PARAMETERS):
    for gibToPopulate in gibs:
        gibToPopulateId = gibToPopulate['id']
        for neighbouringGib in gibs:
            neighbourId = neighbouringGib['id']
            if gibToPopulateId != neighbourId:
                if gibToPopulate['coveredByNeighbour'][neighbourId] == True:
                    gifFrames = []
                    populateSeam(gibToPopulate, gibs, neighbourId, shipImage, tilesets, gifFrames, PARAMETERS)
                    saveGif(gifFrames, '%s_gib%uto%u' % (shipImageName, gibToPopulateId, neighbourId), PARAMETERS)


def populateSeam(gibToPopulate, gibs, neighbourId, shipImage, tilesets, gifFrames, PARAMETERS):
    cleanUpMemory()
    gibImage = gibToPopulate['img']
    originalGibImageArray = np.ma.copy(gibImage)
    seamCoordinates = deepcopy(gibToPopulate['neighbourToSeam'][neighbourId])
    metalBits = np.zeros(shipImage.shape, dtype=np.uint8)
    tilesToUse = tilesets[LAYER1]
    # TODO: use seamCoordinates directly?
    for coordinates in seamCoordinates:
        metalBits[coordinates[0], coordinates[1]] = REMAINING_UNCOVERED_SEAM_PIXEL_COLOR
    # metalBits[np.asarray(seamCoordinates)] = [0, 255, 0, 255]
    seamImageArray = np.ma.copy(metalBits)
    # TODO: for currentLayer in range(1, 4 + 1): or layer function as variable/parameter, or ...
    nrAttemptsForLayer = 1
    remainingUncoveredSeamPixels = np.where(np.all(metalBits == REMAINING_UNCOVERED_SEAM_PIXEL_COLOR, axis=-1))
    while np.any(remainingUncoveredSeamPixels):
        nrAttemptsForLayer += 1
        cleanUpMemory()
        metalBits, remainingUncoveredSeamPixels = attemptTileAttachment(PARAMETERS, gibToPopulate, gibs, gifFrames,
                                                                        metalBits, originalGibImageArray,
                                                                        remainingUncoveredSeamPixels, seamCoordinates,
                                                                        seamImageArray, shipImage, tilesToUse)

    pasteNonTransparentValuesIntoArray(originalGibImageArray, metalBits)
    gibToPopulate['img'] = metalBits


def attemptTileAttachment(PARAMETERS, gibToPopulate, gibs, gifFrames, metalBits, originalGibImageArray,
                          remainingUncoveredSeamPixels, seamCoordinates, seamImageArray, shipImage, tilesToUse):
    isCandidateOriginCoveredByGib = False
    isCandidateValid = False

    attachmentPoint, isDetectionSuccessful, outwardAngle, outwardVectorYX = determineAttachmentPointWithOrientation(
        PARAMETERS, gifFrames, metalBits, originalGibImageArray, remainingUncoveredSeamPixels, seamCoordinates)
    if isDetectionSuccessful == True:
        inwardsSearchX, inwardsSearchY, isCandidateOriginCoveredByGib, tileImageArray, tileOriginCenterPoint = determineCandidateTileWithCoveredOrigin(
            PARAMETERS, attachmentPoint, gifFrames, metalBits, originalGibImageArray, outwardAngle,
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
                                                                   originalGibImageArray, seamPixelsCoveredByCandidate)
    remainingUncoveredSeamPixels = updateRemainingSeamPoints(attachmentPoint, metalBits)
    return metalBits, remainingUncoveredSeamPixels


def approveCandidate(PARAMETERS, gifFrames, metalBitsCandidate, originalGibImageArray,
                     seamPixelsCoveredByCandidate):
    metalBits = metalBitsCandidate
    remainingUncoveredSeamPixels = updateRemainingSeamPoints(seamPixelsCoveredByCandidate, metalBits)
    animateGibResultAndSeamPreview(PARAMETERS, gifFrames, metalBits, originalGibImageArray,
                                   remainingUncoveredSeamPixels)
    return metalBits, remainingUncoveredSeamPixels


def animateBlockingImage(PARAMETERS, gifFrames, metalBitsCandidate, gibs, isCandidateValid, blockingNeighbourId,
                         shipImage):
    if PARAMETERS.ANIMATE_METAL_BITS_FOR_DEVELOPER == True and isCandidateValid == False:
        if blockingNeighbourId == 'entireShip':
            blockingImage = np.ma.copy(shipImage)
        else:
            for gib in gibs:
                if gib['id'] == blockingNeighbourId:
                    gibImage = gib['img']
                    blockingImage = np.ma.copy(gibImage)
        blockingImage[np.any(blockingImage != [0, 0, 0, 0], axis=-1)] = [255, 0, 0, 0]
        gifFrame = np.ma.copy(blockingImage)
        pasteNonTransparentValuesIntoArray(metalBitsCandidate, gifFrame)
        gifFrames.append(gifFrame)


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
    isCandidateValid, blockingNeighbourId = doesCandidateSatisfyConstraints(gibToPopulate, gibs, metalBitsCandidate,
                                                                            shipImage)
    animateBlockingImage(PARAMETERS, gifFrames, metalBitsCandidate, gibs, isCandidateValid, blockingNeighbourId,
                         shipImage)
    return isCandidateValid, metalBitsCandidate, seamPixelsCoveredByCandidate


def determineCandidateTileWithCoveredOrigin(PARAMETERS, attachmentPoint, gifFrames, metalBits, originalGibImageArray,
                                            outwardAngle, outwardVectorYX, tilesToUse):
    tileImageArray, tileOriginCenterPoint, tileOriginCoordinates = determineTileToAttach(outwardAngle,
                                                                                         tilesToUse)
    alreadyCoveredArea = np.ma.copy(originalGibImageArray)
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
        gifFrame = np.ma.copy(metalBits)
        pasteNonTransparentValuesIntoArray(originalGibImageArray, gifFrame)
        gifFrames.append(gifFrame)
        gifFrameNextSeamPixels = np.ma.copy(gifFrame)
        gifFrameNextSeamPixels[remainingUncoveredSeamPixels] = REMAINING_UNCOVERED_SEAM_PIXEL_COLOR
        gifFrames.append(gifFrameNextSeamPixels)


def animateUnverifiedCandidateAttached(PARAMETERS, attachmentPoint, gifFrames, metalBitsCandidate,
                                       originalGibImageArray):
    if PARAMETERS.ANIMATE_METAL_BITS_FOR_DEVELOPER == True:
        gifFrame = np.ma.copy(originalGibImageArray)
        try:
            pasteNonTransparentValuesIntoArray(metalBitsCandidate, gifFrame)
        except:
            pass
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
            gifFrame = np.ma.copy(alreadyCoveredArea)
            for offsetCoordinate in offsetCoordinates:
                try:
                    gifFrame[offsetCoordinate[0], offsetCoordinate[1]] = [0, 0, 255, 255]
                except IndexError:
                    pass
            gifFrame[attachmentPoint] = ATTACHMENT_POINT_COLOR
            gifFrames.append(gifFrame)

        isCandidateOriginCoveredByGib = areAllCoordinatesContainedInVisibleArea(offsetCoordinates,
                                                                                alreadyCoveredArea)
        logHighestMemoryUsage()

    if PARAMETERS.ANIMATE_METAL_BITS_FOR_DEVELOPER == True:
        gifFrame = np.ma.copy(alreadyCoveredArea)
        if isCandidateOriginCoveredByGib == True:
            color = [0, 255, 0, 255]
        else:
            color = [255, 0, 0, 255]
        for offsetCoordinate in offsetCoordinates:
            try:
                gifFrame[offsetCoordinate[0], offsetCoordinate[1]] = color
            except IndexError:
                pass
        gifFrame[attachmentPoint] = ATTACHMENT_POINT_COLOR
        gifFrames.append(gifFrame)

    return isCandidateOriginCoveredByGib, inwardsSearchX, inwardsSearchY


def animateAlreadyCoveredArea(PARAMETERS, alreadyCoveredArea, attachmentPoint, gifFrames):
    if PARAMETERS.ANIMATE_METAL_BITS_FOR_DEVELOPER == True:
        gifFrame = np.ma.copy(alreadyCoveredArea)
        gifFrame[attachmentPoint] = ATTACHMENT_POINT_COLOR
        gifFrames.append(gifFrame)


def determineTileToAttach(outwardAngle, tilesToUse):
    tileCandidates = tilesToUse[outwardAngle]
    tileId = random.randint(0, len(tileCandidates) - 1)
    tileImageArray = tilesToUse[outwardAngle][tileId]['img']
    tileOriginArea, tileOriginCoordinates, tileOriginCenterPoint = tilesToUse[outwardAngle][tileId]['origin']
    return tileImageArray, tileOriginCenterPoint, tileOriginCoordinates


def updateRemainingSeamPoints(attachmentPoint, metalBits):
    metalBits[attachmentPoint] = BLOCKED_SEAM_PIXELS_COLOR
    remainingUncoveredSeamPixels = np.where(np.all(metalBits == REMAINING_UNCOVERED_SEAM_PIXEL_COLOR, axis=-1))
    return remainingUncoveredSeamPixels


def animateAttachmentPointWithOrientation(PARAMETERS, attachmentPoint, gifFrames, isDetectionSuccessful, metalBits,
                                          originalGibImageArray, outwardVectorYX, remainingUncoveredSeamPixels,
                                          seamCoordinates):
    if PARAMETERS.ANIMATE_METAL_BITS_FOR_DEVELOPER == True:
        gifFrame = np.ma.copy(metalBits)
        pasteNonTransparentValuesIntoArray(originalGibImageArray, gifFrame)
        edgeCoordinatesInRadiusY, edgeCoordinatesInRadiusX = findEdgePixelsInSearchRadius(seamCoordinates,
                                                                                          attachmentPoint,
                                                                                          NEARBY_EDGE_PIXEL_SCAN_RADIUS)
        # TODO: only one needed
        # for coordinates in seamCoordinates:
        #    gifFrame[coordinates[0], coordinates[1]] = [63, 63, 63, 255]
        gifFrame[remainingUncoveredSeamPixels] = REMAINING_UNCOVERED_SEAM_PIXEL_COLOR
        gifFrame[edgeCoordinatesInRadiusY, edgeCoordinatesInRadiusX] = [255, 255, 0, 255]

        lineY_A, lineX_A = line(attachmentPoint[0], attachmentPoint[1],
                                attachmentPoint[0] + round(outwardVectorYX[0] * 50),
                                attachmentPoint[1] + round(outwardVectorYX[1] * 50))
        # TODO avoid out of bounds (workaround: uncropped gib which is fine; should be basis later on anyway)
        if isDetectionSuccessful == True:
            try:
                gifFrame[lineY_A, lineX_A] = [0, 127, 255, 255]
            except IndexError:
                logger.warning('Could not render line for gifFrame')
        else:
            try:
                gifFrame[lineY_A, lineX_A] = [255, 127, 0, 255]
            except IndexError:
                logger.warning('Could not render line for gifFrame')
        gifFrame[attachmentPoint] = ATTACHMENT_POINT_COLOR
        gifFrames.append(gifFrame)


def determineAttachmentPoint(remainingUncoveredSeamPixels):
    attachmentPointId = random.randint(0, len(remainingUncoveredSeamPixels[0]) - 1)
    attachmentPoint = remainingUncoveredSeamPixels[0][attachmentPointId], remainingUncoveredSeamPixels[1][
        attachmentPointId]
    return attachmentPoint


def doesCandidateSatisfyConstraints(gibToPopulate, gibs, metalBitsCandidate, shipImage):
    isCandidateValid = areAllVisiblePixelsContained(metalBitsCandidate, shipImage)
    blockingNeighbourId = 'entireShip'
    if isCandidateValid:
        for otherGib in gibs:
            otherGibId = otherGib['id']
            if gibToPopulate['coversNeighbour'][otherGibId] == True:
                if otherGibId != gibToPopulate['id']:
                    if areAnyVisiblePixelsOverlapping(metalBitsCandidate, otherGib['img']) == True:
                        isCandidateValid = False
                        blockingNeighbourId = otherGibId
                        break
                else:
                    logger.critical('Gib should not be covering itself?!')
    return isCandidateValid, blockingNeighbourId
