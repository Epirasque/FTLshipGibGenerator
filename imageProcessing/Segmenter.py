import numpy as np
from skimage.segmentation import slic

# TODO: remove shipImageName as parameter
from imageProcessing.ImageProcessingUtilities import cropImage

TRANSPARENCY_ALPHA_VALUE = 0


def segment(shipImage, shipImageName, nrGibs, segmentQuickAndDirty):
    nonTransparentMask = (shipImage[:, :, 3] != TRANSPARENCY_ALPHA_VALUE)
    nrSuccessfulGibs = 0
    nrSegmentationAttempts = 0
    compactnessToUse = 0.2  # TODO: start with 0. ?
    compactnessGainPerAttempt = 0.1
    nrMaximumSegmentationAttempts = 13
    if segmentQuickAndDirty == True:
        compactnessToUse = 1.
        nrMaximumSegmentationAttempts = 1
    while nrSuccessfulGibs < nrGibs and nrSegmentationAttempts < nrMaximumSegmentationAttempts:  # TODO: proper nr attempts approach
        nrSegmentationAttempts += 1
        compactnessToUse += compactnessGainPerAttempt  # TODO: make configurable
        # TODO: parameter for max iterations of kmeans
        # TODO: upon failure, retry with less/more gibs
        segments = slic(shipImage, n_segments=nrGibs, compactness=compactnessToUse, max_num_iter=100,
                        mask=nonTransparentMask)
        nrSuccessfulGibs = segments.max()
    if nrSuccessfulGibs == 0:
        print("FAILED to generate any gibs for %s" % shipImageName)
        return []
    if nrSuccessfulGibs < nrGibs:
        print("Did not generate all gibs for %s, ended up with %u of %u" % (shipImageName, nrSuccessfulGibs, nrGibs))
        nrGibs = nrSuccessfulGibs
    if nrSegmentationAttempts > 1:
        print("Segmented with %u attempts with compactness of %f " % (nrSegmentationAttempts, compactnessToUse))
    return turnSegmentsIntoGibs(nrGibs, segments, shipImage)


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
