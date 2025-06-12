import numpy as np
from scipy.ndimage import convolve

from imageProcessing.ImageProcessingUtilities import getFullyTransparentPixels


def removeGlow(imageArray):
    nrGlowPixels = -1
    while nrGlowPixels != 0:
        fullyTransparentPixels = getFullyTransparentPixels(imageArray)
        # may not check diagonally, solid edges can be diagonal 1-pixel-lines
        anyNeighbourButNotSelfKernel = np.array([[0, 1, 0], [1, -10, 1], [0, 1, 0]])
        fullyTransparentMask = np.zeros((imageArray.shape[0], imageArray.shape[1]), dtype=np.int8)
        fullyTransparentMask[fullyTransparentPixels] = 1

        neighbourToFullyTransparent = convolve(fullyTransparentMask, anyNeighbourButNotSelfKernel, mode='constant', cval=1)

        partiallyTransparentPixels = np.nonzero(~imageArray[:, :, 3])
        partiallyTransparentMask = np.zeros((imageArray.shape[0], imageArray.shape[1]), dtype=np.int8)
        partiallyTransparentMask[partiallyTransparentPixels] = 1

        glowPixels = np.where((neighbourToFullyTransparent > 0) & partiallyTransparentMask == 1)
        nrGlowPixels = len(glowPixels[0])
        imageArray[glowPixels] = [0, 0, 0, 0]

    return imageArray
