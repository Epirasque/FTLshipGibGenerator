from skimage.segmentation import slic
import imageio
import numpy as np

#TODO: remove shipImageName as parameter
def segment(shipImage, shipImageName, nrGibs):
    transparency_mask = (shipImage[:, :, 3] != 0)
    nrSuccessfulGibs = 0
    nrSegmentationAttempts = 0
    compactnessToUse = 0.
    while nrSuccessfulGibs < nrGibs and nrSegmentationAttempts < 10:
        nrSegmentationAttempts += 1
        compactnessToUse += 1.0 # TODO: change back to 0.1 or rather make configurable
        # TODO: parameter for max iterations of kmeans
        segments = slic(shipImage, n_segments=nrGibs, compactness=compactnessToUse, max_num_iter=10,
                        mask=transparency_mask)
        nrSuccessfulGibs = segments.max()
    if nrSuccessfulGibs < nrGibs:
        print("FAILED generating gibs for %s" % shipImageName)
        return []
    else:
        #print("Segmented with %u attempts with compactness of %f " % (nrSegmentationAttempts, compactnessToUse))
        gibs = []
        for gibId in range(1, nrGibs + 1):
            matchingSegmentIndex = (segments == gibId)
            gibImage = np.zeros(shipImage.shape, dtype=np.uint8)
            gibImage[matchingSegmentIndex] = shipImage[matchingSegmentIndex]
            gib = {}
            gib['id'] = gibId
            gib['img'] = gibImage
            gibs.append(gib)

            # TODO: toggle to disable it here
            #imageio.imsave('gibs/' + shipImageName + '_gib_' + str(gibId) + '.png', gibImage)
        return gibs
