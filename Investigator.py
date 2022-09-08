import sys

import numpy as np
from skimage.io import imread
from scipy.ndimage import convolve
from PIL import Image

def main(argv):
    folder = 'investigation\\thin_line_removal\\'
    imageArray = imread(folder + '6.png')
    transparentPixels = np.nonzero(~imageArray[:, :, 3])
    mask = np.zeros((imageArray.shape[0], imageArray.shape[1]), dtype=np.int8)
    mask[transparentPixels] = 1
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


if __name__ == '__main__':
    main(sys.argv)