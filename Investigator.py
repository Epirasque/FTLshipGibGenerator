import sys

import numpy as np
from skimage.io import imread
from scipy.ndimage import convolve
from PIL import Image

from imageProcessing.ImageProcessingUtilities import getFullyTransparentPixels


def investigateGlowRemoval():
    folder = 'investigation\\glow_removal\\'
    imageArray = imread(folder + 'enclosed_transparency_and_glow.png')

    nrGlowPixels = -1
    while nrGlowPixels != 0:
        fullyTransparentPixels = getFullyTransparentPixels(imageArray)
        # may not check diagonally, solid edges can be diagonal 1-pixel-lines
        anyNeighbourButNotSelfKernel = np.array([[0, 1, 0], [1, -10, 1], [0, 1, 0]])
        fullyTransparentMask = np.zeros((imageArray.shape[0], imageArray.shape[1]), dtype=np.int8)
        fullyTransparentMask[fullyTransparentPixels] = 1

        neighbourToFullyTransparent = convolve(fullyTransparentMask, anyNeighbourButNotSelfKernel, mode='constant', cval=1)

        #neighbourToFullyTransparentMask = np.zeros((imageArray.shape[0], imageArray.shape[1]), dtype=np.int8)
        #neighbourToFullyTransparentMask[neighbourToFullyTransparent > 0] = 1

        partiallyTransparentPixels = np.nonzero(~imageArray[:, :, 3])
        partiallyTransparentMask = np.zeros((imageArray.shape[0], imageArray.shape[1]), dtype=np.int8)
        partiallyTransparentMask[partiallyTransparentPixels] = 1

        glowPixels = np.where((neighbourToFullyTransparent > 0) & partiallyTransparentMask == 1)
        nrGlowPixels = len(glowPixels[0])
        print(nrGlowPixels)
        imageArray[glowPixels] = [0, 0, 0, 0]

    Image.fromarray(imageArray).show()

def investigateThinLineRemoval():
    folder = 'investigation\\thin_line_removal\\'
    imageArray = imread(folder + '6.png')
    partiallyTransparentPixels = np.nonzero(~imageArray[:, :, 3])
    mask = np.zeros((imageArray.shape[0], imageArray.shape[1]), dtype=np.int8)
    mask[partiallyTransparentPixels] = 1
    kernel=np.array([[1,1,1],[1,10,1],[1,1,1]]) # consider bigger one? for 2 pixel width lines, and MAYBE get rid off 2nd mask

    convolutedMask = convolve(mask, kernel, mode='constant', cval=1)
    newMask = np.zeros((imageArray.shape[0], imageArray.shape[1]), dtype=np.int8)
    newMask[convolutedMask >= (8-2)] = 1

    convolutedNewMask = convolve(newMask, kernel, mode='constant', cval=1)
    newestMask = np.zeros((imageArray.shape[0], imageArray.shape[1]), dtype=np.int8)
    newestMask[convolutedNewMask >= (8-2)] = 1

    convolutedNewestMask = convolve(newestMask, kernel, mode='constant', cval=1)

    #imageArray[transparentPixels] = [63,0,0,255]

    imageArray[np.where((convolutedNewestMask >= (8-2)) & (mask == 0))] = [0,255,0,255]
    Image.fromarray(imageArray).show()

def main(argv):
    #investigateThinLineRemoval()
    investigateGlowRemoval()

if __name__ == '__main__':
    main(sys.argv)