import numpy as np


# takes numpy array and RGB color of the filter in form of an array
def findColorInImage(imageArray, colorToFind):
    nonColorMask = np.where(np.any(imageArray != [colorToFind[0], colorToFind[1], colorToFind[2], 255], axis=-1))
    coloredArea = imageArray.copy()
    coloredArea[nonColorMask] = [0, 0, 0, 0]

    coloredCoordinates = np.argwhere(coloredArea)
    coloredCoordinates = np.delete(coloredCoordinates, 2, 1)
    coloredCoordinates = np.unique(coloredCoordinates, axis=0)
    return coloredArea, coloredCoordinates

def pasteNonBlackValuesIntoArray(source, target):
    colorMaskCoordinates = np.where(np.all(source != [0, 0, 0, 0], axis=-1))
    target[colorMaskCoordinates[0], colorMaskCoordinates[1],:] = source[colorMaskCoordinates[0], colorMaskCoordinates[1],:]

#def findNotColorInImage(imageArray, colorToAvoid):
#    colorMask = np.where(np.all(imageArray != [colorToAvoid[0], colorToAvoid[1], colorToAvoid[2], 255], axis=-1))
#    coloredArea = imageArray.copy()
#    coloredArea[colorMask] = [0, 0, 0, 0]
#
#    coloredCoordinates = np.argwhere(coloredArea)
#    coloredCoordinates = np.delete(coloredCoordinates, 2, 1)
#    coloredCoordinates = np.unique(coloredCoordinates, axis=0)
#    return coloredArea, coloredCoordinates


def getDistanceBetweenPoints(x1, y1, x2, y2):
    return np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
