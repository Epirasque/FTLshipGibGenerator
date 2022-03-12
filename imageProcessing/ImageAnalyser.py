import numpy as np


# takes numpy array and RGB color of the filter in form of an array
def filterColorInImage(image, filterColor):
    nonColorMask = np.where(np.any(image != [filterColor[0], filterColor[1], filterColor[2], 255], axis=-1))
    coloredArea = image.copy()
    coloredArea[nonColorMask] = [0, 0, 0, 0]

    edgeCoordinates = np.argwhere(coloredArea)
    edgeCoordinates = np.delete(edgeCoordinates, 2, 1)
    edgeCoordinates = np.unique(edgeCoordinates, axis=0)
    return coloredArea, edgeCoordinates


def getDistanceBetweenPoints(x1, y1, x2, y2):
    return np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
