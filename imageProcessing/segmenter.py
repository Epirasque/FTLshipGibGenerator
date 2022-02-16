from skimage.segmentation import slic
import imageio
import numpy as np
from numpy import mean


# TODO: remove shipImageName as parameter
def segment(shipImage, shipImageName, nrGibs, segmentQuickAndDirty):
    nonTranspartMask = (shipImage[:, :, 3] != 0)
    nrSuccessfulGibs = 0
    nrSegmentationAttempts = 0
    compactnessToUse = 0.2  # TODO: start with 0. ?
    compactnessGainPerAttempt = 0.1
    nrMaximumSegmentationAttempts = 13
    if segmentQuickAndDirty:
        compactnessToUse = 1.
        nrMaximumSegmentationAttempts = 1
    while nrSuccessfulGibs < nrGibs and nrSegmentationAttempts < nrMaximumSegmentationAttempts:  # TODO: proper nr attempts approach
        nrSegmentationAttempts += 1
        compactnessToUse += compactnessGainPerAttempt  # TODO: make configurable
        # TODO: parameter for max iterations of kmeans
        # TODO: upon failure, retry with less/more gibs
        segments = slic(shipImage, n_segments=nrGibs, compactness=compactnessToUse, max_num_iter=100,
                        mask=nonTranspartMask)
        nrSuccessfulGibs = segments.max()
    if nrSuccessfulGibs < nrGibs:
        print("FAILED generating gibs for %s" % shipImageName)
        return []
    else:
        if nrSegmentationAttempts > 1:
            print("Segmented with %u attempts with compactness of %f " % (nrSegmentationAttempts, compactnessToUse))
        gibs = []
        # TODO: sort gibs by velocity (maybe just mass) so faster ones are on top
        for gibId in range(1, nrGibs + 1):
            matchingSegmentIndex = (segments == gibId)
            gibImage = np.zeros(shipImage.shape, dtype=np.uint8)
            gibImage[matchingSegmentIndex] = shipImage[matchingSegmentIndex]
            croppedGibImage, center, minX, minY = crop(gibImage)
            # TODO: reenable, but its slow nrVisiblePixels = sum(matchingSegmentIndex.flatten() == True)

            gib = {}
            gib['id'] = gibId
            gib['img'] = croppedGibImage
            gib['center'] = center
            gib['x'] = minX
            gib['y'] = minY
            gib['mass'] = (center['x'] - minX) * (center['y'] - minY) * 4  # TODO: reenable nrVisiblePixels
            gibs.append(gib)

        return gibs


def crop(image):
    visiblePixelsY, visiblePixelsX = np.nonzero(image[:, :, 3])
    minX = min(visiblePixelsX)
    maxX = max(visiblePixelsX)
    minY = min(visiblePixelsY)
    maxY = max(visiblePixelsY)
    croppedImage = image[minY:maxY, minX:maxX, :]
    # TODO: consider center of gravity instead?
    center = {}
    center['x'] = (maxX + minX) / 2
    center['y'] = (maxY + minY) / 2
    return croppedImage, center, minX, minY
