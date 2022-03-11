import numpy as np


def cropImage(image):
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
