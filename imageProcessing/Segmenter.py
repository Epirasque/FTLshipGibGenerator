import logging

import numpy as np
from PIL import Image
from skimage.segmentation import slic

# TODO: remove shipImageName as parameter
from flow.MemoryManagement import cleanUpMemory
from imageProcessing.ImageProcessingUtilities import cropImage, imageDifferenceInPercentage

# glow around ships should not be part of the gibs
VISIBLE_ALPHA_VALUE = 255
MAXIMUM_DEVIATION_FROM_BASE_IMAGE_PERCENTAGE = 1.

logger = logging.getLogger('GLAIVE.' + __name__)


def segment(shipImage, shipImageName, nrGibs, segmentQuickAndDirty):
    nonTransparentMask = (shipImage[:, :, 3] == VISIBLE_ALPHA_VALUE)
    nrSuccessfulGibs = 0
    nrSegmentationAttempts = 0
    compactnessToUse = 0.3
    compactnessGainPerAttempt = 0.05
    compactnessThreshold = 2.5
    percentage = 100.
    if segmentQuickAndDirty == True:
        compactnessToUse = 1.
        compactnessGainPerAttempt = 0.5
    # compensate for first increment
    compactnessToUse -= compactnessGainPerAttempt
    while (
            nrSuccessfulGibs < nrGibs or percentage > MAXIMUM_DEVIATION_FROM_BASE_IMAGE_PERCENTAGE) and compactnessToUse < compactnessThreshold:  # TODO: proper nr attempts approach
        nrSegmentationAttempts += 1
        compactnessToUse += compactnessGainPerAttempt  # TODO: make configurable
        cleanUpMemory()
        # TODO: parameter for max iterations of kmeans
        # TODO: upon failure, retry with less/more gibs
        # TODO: try additional parameters e.g. channel-axis
        segments = slic(shipImage, n_segments=nrGibs, compactness=compactnessToUse, max_num_iter=100,
                        mask=nonTransparentMask)
        nrSuccessfulGibs = determineNrSuccessfulGibs(segments, nrGibs)
        if nrSuccessfulGibs == nrGibs:
            percentage = determinePixelDeviationPercentageByReconstructingBaseWithSegments(segments, nrSuccessfulGibs,
                                                                                           shipImage)
            if percentage > MAXIMUM_DEVIATION_FROM_BASE_IMAGE_PERCENTAGE:
                logger.warning(
                    "Retrying due to gibs not combining into base image for %s, pixel deviation is at %.2f%%, which is above allowed threshold of %.2f%%" % (
                        shipImageName, percentage, MAXIMUM_DEVIATION_FROM_BASE_IMAGE_PERCENTAGE))
    if nrSuccessfulGibs == 0:
        logger.error("FAILED to generate any gibs for %s" % shipImageName)
        return []
    if percentage > MAXIMUM_DEVIATION_FROM_BASE_IMAGE_PERCENTAGE:
        logger.error(
            "Reconstructing ship from gibs for %s deviates by %.2f%% pixels, which is above allowed threshold of %.2f%%" % (
                shipImageName, percentage, MAXIMUM_DEVIATION_FROM_BASE_IMAGE_PERCENTAGE))
    if nrSuccessfulGibs < nrGibs:
        # TODO: consider it a failure instead?
        logger.error(
            "Did not generate all gibs for %s, ended up with %u of %u" % (shipImageName, nrSuccessfulGibs, nrGibs))
        nrGibs = nrSuccessfulGibs
    if nrSegmentationAttempts > 1:
        logger.debug("Segmented with %u attempts with compactness of %f " % (nrSegmentationAttempts, compactnessToUse))
    return turnSegmentsIntoGibs(nrGibs, segments, shipImage)


def determinePixelDeviationPercentageByReconstructingBaseWithSegments(segments, nrSuccessfulGibs, shipImage):
    reconstructedFromSegments = Image.fromarray(np.zeros(shipImage.shape, dtype=np.uint8))
    for gibId in range(1, nrSuccessfulGibs + 1):
        matchingSegmentIndex = (segments == gibId)
        gibImage = np.zeros(shipImage.shape, dtype=np.uint8)
        gibImage[matchingSegmentIndex] = shipImage[matchingSegmentIndex]
        reconstructedFromSegments.paste(Image.fromarray(gibImage), (0, 0), Image.fromarray(gibImage))
    return imageDifferenceInPercentage(shipImage, reconstructedFromSegments)


def determineNrSuccessfulGibs(segments, nrGibs):
    nrSuccessfulGibs = 0
    for gibId in range(1, nrGibs + 1):
        if moreThanOnePoint(gibId, segments) and moreThanOneDistinctYvalue(gibId,
                                                                           segments) and moreThanOneDistinctXvalue(
            gibId, segments):
            nrSuccessfulGibs += 1
    return nrSuccessfulGibs


def moreThanOneDistinctXvalue(gibId, segments):
    return min(np.where(segments == gibId)[1]) < max(
        np.where(segments == gibId)[1])


def moreThanOneDistinctYvalue(gibId, segments):
    return min(np.where(segments == gibId)[0]) < max(
        np.where(segments == gibId)[0])


def moreThanOnePoint(gibId, segments):
    return len(np.where(segments == gibId)[0]) > 1


def turnSegmentsIntoGibs(nrGibs, segments, shipImage):
    gibs = []
    # TODO: sort gibs by velocity (maybe just mass) so faster ones are on top
    for gibId in range(1, nrGibs + 1):
        matchingSegmentIndex = (segments == gibId)
        gibImage = np.zeros(shipImage.shape, dtype=np.uint8)
        gibImage[matchingSegmentIndex] = shipImage[matchingSegmentIndex]
        croppedGibImage, center, minX, minY = cropImage(gibImage)
        # TODO: reenable, but its slow nrVisiblePixels = sum(matchingSegmentIndex.flatten() == True)

        gib = {}
        gib['id'] = gibId
        gib['z'] = gibId
        gib['img'] = croppedGibImage
        gib['center'] = center
        gib['x'] = minX
        gib['y'] = minY
        gib['mass'] = (center['x'] - minX) * (center['y'] - minY) * 4  # TODO: reenable nrVisiblePixels
        gibs.append(gib)
    return gibs
