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


def pasteNonTransparentBlackValuesIntoArray(source, target):
    colorMaskCoordinates = np.where(np.any(source != [0, 0, 0, 0], axis=-1))
    target[colorMaskCoordinates[0], colorMaskCoordinates[1], :] = source[colorMaskCoordinates[0],
                                                                  colorMaskCoordinates[1], :]


def areVisiblePixelsOverlapping(imageArrayA, imageArrayB):
    return np.any(np.any(imageArrayA != [0, 0, 0, 0], axis=-1) & np.any(imageArrayB != [0, 0, 0, 0], axis=-1))


def areAllVisiblePixelsContained(innerImageArray, outerImageArray):
    innerImageVisibleMask = np.any(innerImageArray != [0, 0, 0, 0], axis=-1)
    outerImageVisiblePoints = np.where(np.any(outerImageArray != [0, 0, 0, 0], axis=-1))
    innerImageVisibleMask[outerImageVisiblePoints[0], outerImageVisiblePoints[1]] = False
    return not np.any(innerImageVisibleMask)


# def findNotColorInImage(imageArray, colorToAvoid):
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
