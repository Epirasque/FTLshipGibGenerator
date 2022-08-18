import random
import traceback

from skimage.draw import line

from fileHandling.MetalBitsLoader import LAYER1, LAYER3
from flow.GeneratorLooper import logHighestMemoryUsage
from flow.MemoryManagement import cleanUpMemory
from imageProcessing.DebugAnimator import saveGif
from imageProcessing.ImageProcessingUtilities import *
from imageProcessing.MetalBitsConstants import *


def populateSeams(gibs, shipImageName, shipImage, tilesets, shipColorMean, PARAMETERS):
    for gibToPopulate in gibs:
        gibToPopulateId = gibToPopulate['id']
        for neighbouringGib in gibs:
            neighbourId = neighbouringGib['id']
            if gibToPopulateId != neighbourId:
                if gibToPopulate['coveredByNeighbour'][neighbourId] == True:
                    gifFrames = []
                    populateSeam(gibToPopulate, gibs, neighbourId, shipImage, tilesets, gifFrames, shipColorMean,
                                 PARAMETERS)
                    saveGif(gifFrames, '%s_gib%uto%u' % (shipImageName, gibToPopulateId, neighbourId), PARAMETERS)


def populateSeam(gibToPopulate, gibs, neighbourId, shipImage, tilesets, gifFrames, shipColorMean, PARAMETERS):
    cleanUpMemory()
    gibImage = gibToPopulate['img']
    originalGibImageArray = np.ma.copy(gibImage)  # todo: use this more often? more efficient?
    seamCoordinates = deepcopy(gibToPopulate['neighbourToSeam'][neighbourId])
    seamDistanceScores = precalculateSeamDistanceScores(seamCoordinates)
    metalBitsLayer1AndBeyond = populateLayer1(PARAMETERS, gibToPopulate, gibs, gifFrames, originalGibImageArray,
                                              seamCoordinates,
                                              seamDistanceScores, shipImage,
                                              tilesets,
                                              shipColorMean)  # TODO new seamCoordinates = deepcopy(gibToPopulate['neighbourToSeam'][neighbourId])
    metalBitsLayer3 = populateLayer3(PARAMETERS, gibToPopulate, gibs, gifFrames, originalGibImageArray, seamCoordinates,
                                     seamDistanceScores, shipImage, tilesets, shipColorMean)
    try:
        pasteNonTransparentValuesIntoArray(metalBitsLayer3, metalBitsLayer1AndBeyond)
        finalGib = deepcopy(metalBitsLayer1AndBeyond)
        pasteNonTransparentValuesIntoArray(originalGibImageArray, finalGib)
    except Exception:
        logger = getSubProcessLogger()
        logger.error("UNEXPECTED EXCEPTION: %s" % traceback.format_exc())
    gibToPopulate['img'] = finalGib
    gibToPopulate['uncropped_metalbits'] = deepcopy(metalBitsLayer1AndBeyond)
    removeNonTransparentValuesFromArray(originalGibImageArray, gibToPopulate['uncropped_metalbits'])


def populateLayer1(PARAMETERS, gibToPopulate, gibs, gifFrames, originalGibImageArray, seamCoordinates,
                   seamDistanceScores, shipImage, tilesets, shipColorMean):
    metalBits = np.zeros(shipImage.shape, dtype=np.uint8)
    tilesToUse = tilesets[LAYER1]
    # TODO: use seamCoordinates directly?
    for coordinates in seamCoordinates:
        metalBits[coordinates[0], coordinates[1]] = REMAINING_UNCOVERED_SEAM_PIXEL_COLOR
    # metalBits[np.asarray(seamCoordinates)] = [0, 255, 0, 255]
    seamImageArray = np.ma.copy(metalBits)
    remainingUncoveredSeamPixels = np.where(np.all(metalBits == REMAINING_UNCOVERED_SEAM_PIXEL_COLOR, axis=-1))
    while np.any(remainingUncoveredSeamPixels):
        cleanUpMemory()
        metalBits, remainingUncoveredSeamPixels, isCandidateValid = attemptTileAttachment(PARAMETERS, gibToPopulate,
                                                                                          gibs, gifFrames,
                                                                                          metalBits,
                                                                                          originalGibImageArray,
                                                                                          remainingUncoveredSeamPixels,
                                                                                          seamCoordinates,
                                                                                          seamImageArray, shipImage,
                                                                                          tilesToUse,
                                                                                          seamDistanceScores,
                                                                                          shipColorMean)
    return metalBits


def populateLayer3(PARAMETERS, gibToPopulate, gibs, gifFrames, originalGibImageArray, seamCoordinates,
                   seamDistanceScores, shipImage, tilesets, shipColorMean):
    metalBits = np.zeros(shipImage.shape, dtype=np.uint8)
    tilesToUse = tilesets[LAYER3]
    # TODO: use seamCoordinates directly?
    for coordinates in seamCoordinates:
        metalBits[coordinates[0], coordinates[1]] = REMAINING_UNCOVERED_SEAM_PIXEL_COLOR
    # metalBits[np.asarray(seamCoordinates)] = [0, 255, 0, 255]
    seamImageArray = np.ma.copy(metalBits)
    # TODO: for currentLayer in range(1, 4 + 1): or layer function as variable/parameter, or ...
    remainingUncoveredSeamPixels = np.where(np.all(metalBits == REMAINING_UNCOVERED_SEAM_PIXEL_COLOR, axis=-1))
    cleanUpMemory()
    isCandidateValid = False
    while isCandidateValid == False and np.any(remainingUncoveredSeamPixels):
        metalBits, remainingUncoveredSeamPixels, isCandidateValid = attemptTileAttachment(PARAMETERS, gibToPopulate,
                                                                                          gibs, gifFrames,
                                                                                          metalBits,
                                                                                          originalGibImageArray,
                                                                                          remainingUncoveredSeamPixels,
                                                                                          seamCoordinates,
                                                                                          seamImageArray, shipImage,
                                                                                          tilesToUse,
                                                                                          seamDistanceScores,
                                                                                          shipColorMean)
    return metalBits


def precalculateSeamDistanceScores(seamCoordinates):
    seamDistanceScores = {}
    for coordinates in seamCoordinates:
        for distanceCoordinates in seamCoordinates:
            squaredDistance = ((coordinates[0] - distanceCoordinates[0]) ** 2
                               + (coordinates[1] - distanceCoordinates[1]) ** 2)
            if squaredDistance > 0:  # occurs for distance to itself
                seamDistanceScores[coordinates, distanceCoordinates] = 1. / squaredDistance
            else:
                seamDistanceScores[coordinates, distanceCoordinates] = 0
    return seamDistanceScores


def attemptTileAttachment(PARAMETERS, gibToPopulate, gibs, gifFrames, metalBits, originalGibImageArray,
                          remainingUncoveredSeamPixels, seamCoordinates, seamImageArray, shipImage, tilesToUse,
                          seamDistanceScores, shipColorMean):
    isCandidateOriginCoveredByGib = False
    isCandidateValid = False

    attachmentPoint, isDetectionSuccessful, outwardAngle, outwardVectorYX = determineAttachmentPointWithOrientation(
        PARAMETERS, gifFrames, metalBits, originalGibImageArray, remainingUncoveredSeamPixels, seamCoordinates,
        seamDistanceScores)
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
                                                                                                     tileOriginCenterPoint,
                                                                                                     shipColorMean)
    if isCandidateValid == True:
        metalBits, remainingUncoveredSeamPixels = approveCandidate(PARAMETERS, gifFrames, metalBitsCandidate,
                                                                   originalGibImageArray, seamPixelsCoveredByCandidate)
    remainingUncoveredSeamPixels = updateRemainingSeamPoints(attachmentPoint, metalBits)
    return metalBits, remainingUncoveredSeamPixels, isCandidateValid


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
                            tileOriginCenterPoint, shipColorMean):
    tileImageArray = shadeImage(tileImageArray, shipColorMean, random.uniform(0.2, 0.7))
    metalBitsCandidate, seamPixelsCoveredByCandidate, isCandidateValidInitially = constructMetalBitsCandidateBelowMetalBits(
        inwardsSearchX,
        inwardsSearchY,
        metalBits,
        seamImageArray,
        tileImageArray,
        tileOriginCenterPoint)
    if not isCandidateValidInitially:
        isCandidateValid = False
    else:
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
                                            remainingUncoveredSeamPixels, seamCoordinates, seamDistanceScores):
    attachmentPoint = determineAttachmentPoint(remainingUncoveredSeamPixels, seamDistanceScores)
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
    isCandidateValidInitially = True
    metalBitsCandidate = np.zeros(metalBits.shape, dtype=np.uint8)
    try:
        pasteNonTransparentValuesIntoArrayWithOffset(tileImageArray, metalBitsCandidate,
                                                     inwardsSearchY - tileOriginCenterPoint[0],
                                                     inwardsSearchX - tileOriginCenterPoint[1])
    except IndexError:
        logger = getSubProcessLogger()
        logger.debug('Discarding candidate with metal bits stretching out of bounds')
        isCandidateValidInitially = False
    seamPixelsCoveredByCandidate = getVisibleOverlappingPixels(metalBitsCandidate, seamImageArray)
    pasteNonTransparentValuesIntoArray(metalBits, metalBitsCandidate)
    return metalBitsCandidate, seamPixelsCoveredByCandidate, isCandidateValidInitially


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
    logger = getSubProcessLogger()
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


def determineAttachmentPoint(remainingUncoveredSeamPixels, seamDistanceScores):
    candidatePoints = list(zip(remainingUncoveredSeamPixels[0], remainingUncoveredSeamPixels[1]))
    bestScore = 0
    bestCandidatePoint = candidatePoints[0]
    for candidatePoint in candidatePoints:
        score = 0
        for candidateInRange in candidatePoints:
            score += seamDistanceScores[candidatePoint, candidateInRange]
        if score > bestScore:
            bestCandidatePoint = candidatePoint
            bestScore = score
    return bestCandidatePoint


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
                    logger = getSubProcessLogger()
                    logger.critical('Gib should not be covering itself?!')
    return isCandidateValid, blockingNeighbourId
