import numpy as np
from PIL import Image
from skimage.segmentation import slic

# TODO: remove shipImageName as parameter
from imageProcessing.ImageProcessingUtilities import cropImage, imageDifferenceInPercentage

TRANSPARENCY_ALPHA_VALUE = 0
MAXIMUM_DEVIATION_FROM_BASE_IMAGE_PERCENTAGE = 1


def segment(shipImage, shipImageName, nrGibs, segmentQuickAndDirty):
    nonTransparentMask = (shipImage[:, :, 3] != TRANSPARENCY_ALPHA_VALUE)
    nrSuccessfulGibs = 0
    nrSegmentationAttempts = 0
    compactnessToUse = 0.3  # TODO: start with 0. ?
    compactnessGainPerAttempt = 0.1
    nrMaximumSegmentationAttempts = 13
    percentage = 100
    if segmentQuickAndDirty == True:
        compactnessToUse = 1.
        nrMaximumSegmentationAttempts = 1
    while nrSuccessfulGibs < nrGibs and nrSegmentationAttempts < nrMaximumSegmentationAttempts and percentage > MAXIMUM_DEVIATION_FROM_BASE_IMAGE_PERCENTAGE:  # TODO: proper nr attempts approach
        nrSegmentationAttempts += 1
        compactnessToUse += compactnessGainPerAttempt  # TODO: make configurable
        # TODO: parameter for max iterations of kmeans
        # TODO: upon failure, retry with less/more gibs
        # TODO: try additional parameters e.g. channel-axis
        segments = slic(shipImage, n_segments=nrGibs, compactness=compactnessToUse, max_num_iter=100,
                        mask=nonTransparentMask)
        nrSuccessfulGibs = segments.max()
        percentage = determinePixelDeviationPercentageByReconstructingBaseWithSegments(segments, nrSuccessfulGibs,
                                                                                       shipImage)
    if nrSuccessfulGibs == 0:
        print("FAILED to generate any gibs for %s" % shipImageName)
        return []
    if percentage > MAXIMUM_DEVIATION_FROM_BASE_IMAGE_PERCENTAGE:
        print("Reconstructing ship from gibs for %s deviates by %u%% pixels, which is above allowed threshold of %u" % (
            shipImageName, percentage, MAXIMUM_DEVIATION_FROM_BASE_IMAGE_PERCENTAGE))
    if nrSuccessfulGibs < nrGibs:
        # TODO: consider it a failure instead?
        print("Did not generate all gibs for %s, ended up with %u of %u" % (shipImageName, nrSuccessfulGibs, nrGibs))
        nrGibs = nrSuccessfulGibs
    if nrSegmentationAttempts > 1:
        print("Segmented with %u attempts with compactness of %f " % (nrSegmentationAttempts, compactnessToUse))
    return turnSegmentsIntoGibs(nrGibs, segments, shipImage)


def determinePixelDeviationPercentageByReconstructingBaseWithSegments(segments, nrSuccessfulGibs, shipImage):
    reconstructedFromSegments = Image.fromarray(np.zeros(shipImage.shape, dtype=np.uint8))
    for gibId in range(1, nrSuccessfulGibs + 1):
        matchingSegmentIndex = (segments == gibId)
        gibImage = np.zeros(shipImage.shape, dtype=np.uint8)
        gibImage[matchingSegmentIndex] = shipImage[matchingSegmentIndex]
        reconstructedFromSegments.paste(Image.fromarray(gibImage), (0, 0), Image.fromarray(gibImage))
    return imageDifferenceInPercentage(shipImage, reconstructedFromSegments)


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
