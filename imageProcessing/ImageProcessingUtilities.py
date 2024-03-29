import logging
import warnings
from copy import deepcopy

import numpy as np

# takes numpy array and RGB color of the filter in form of an array
from flow.LoggerUtils import getSubProcessLogger


def findColorInImage(imageArray, colorToFind):
    nonColorMask = np.where(np.any(imageArray != [colorToFind[0], colorToFind[1], colorToFind[2], 255], axis=-1))
    coloredArea = imageArray.copy()
    coloredArea[nonColorMask] = [0, 0, 0, 0]

    coloredCoordinates = np.argwhere(coloredArea)
    coloredCoordinates = np.delete(coloredCoordinates, 2, 1)
    coloredCoordinates = [tuple(row) for row in np.unique(coloredCoordinates, axis=0)]
    return coloredArea, coloredCoordinates


def pasteNonTransparentValuesIntoArray(source, target):
    # NOTE: has to ensure source is not altered
    colorMaskCoordinates = np.where(np.any(source != [0, 0, 0, 0], axis=-1))
    target[colorMaskCoordinates[0], colorMaskCoordinates[1], :] = source[colorMaskCoordinates[0],
                                                                  colorMaskCoordinates[1], :]


def removeNonTransparentValuesFromArray(source, target):
    # NOTE: has to ensure source is not altered
    colorMaskCoordinates = np.where(np.any(source != [0, 0, 0, 0], axis=-1))
    target[colorMaskCoordinates[0], colorMaskCoordinates[1], :] = [0, 0, 0, 0]


def pasteNonTransparentValuesIntoArrayWithOffset(source, target, yOffset, xOffset):
    colorMaskCoordinates = np.where(np.any(source != [0, 0, 0, 0], axis=-1))
    target[colorMaskCoordinates[0] + yOffset, colorMaskCoordinates[1] + xOffset, :] = source[colorMaskCoordinates[0],
                                                                                      colorMaskCoordinates[1], :]


def areAnyVisiblePixelsOverlapping(imageArrayA, imageArrayB):
    return np.any(np.any(imageArrayA != [0, 0, 0, 0], axis=-1) & np.any(imageArrayB != [0, 0, 0, 0], axis=-1))


def getVisibleOverlappingPixels(imageArrayA, imageArrayB):
    return np.where(np.any(imageArrayA != [0, 0, 0, 0], axis=-1) & np.any(imageArrayB != [0, 0, 0, 0], axis=-1))


def areAllVisiblePixelsContained(innerImageArray, outerImageArray):
    innerImageVisibleMask = np.any(innerImageArray != [0, 0, 0, 0], axis=-1)
    outerImageVisiblePoints = np.where(np.any(outerImageArray != [0, 0, 0, 0], axis=-1))
    innerImageVisibleMask[outerImageVisiblePoints[0], outerImageVisiblePoints[1]] = False
    return not np.any(innerImageVisibleMask)


def areAllCoordinatesContainedInVisibleArea(coordinates, outerImageArray):
    # TODO: verify by test?
    try:
        for coordinate in coordinates:
            if outerImageArray[coordinate[0], coordinate[1], 3] == 0:
                return False
        return True
        # TODO: performance refactor!
        # return np.all(np.any(outerImageArray[coordinates] != [0, 0, 0, 0], axis=-1))
    except IndexError:
        # outside of image can be assumed to be in a transparent part
        return False


def fitLineToCoordinates(edgeCoordinatesInRadiusY, edgeCoordinatesInRadiusX):
    slope = 0.
    yOffset = 0
    try:
        slope, yOffset = np.polyfit(edgeCoordinatesInRadiusX, edgeCoordinatesInRadiusY, deg=1)
    except:
        logger = getSubProcessLogger()
        logger.warning("WARNING: Failed to detect line among edge pixels within search radius")
    return slope, yOffset


def determineYXorthogonalVectorsForSlope(slope):
    turnedVectorYX_A = normalized([1., -slope])[0]
    turnedVectorYX_B = normalized([-1., slope])[0]
    return turnedVectorYX_A, turnedVectorYX_B


# src: https://stackoverflow.com/questions/21030391/how-to-normalize-a-numpy-array-to-a-unit-vector
def normalized(a, axis=-1, order=2):
    l2 = np.atleast_1d(np.linalg.norm(a, order, axis))
    l2[l2 == 0] = 1
    return a / np.expand_dims(l2, axis)


def vectorToAngleWithNorthBeingZero(outwardVector):
    angle = round(np.arctan2(outwardVector[0], outwardVector[1]) * 180. / np.pi) + 90
    return angle % 360


def determineOutwardDirectionAtPoint(imageArray, edgeCoordinates, pointOfDetection, nearbyEdgePixelScanRadius,
                                     maximumScanForTransparencyDistance):
    edgeCoordinatesInRadiusY, edgeCoordinatesInRadiusX = findEdgePixelsInSearchRadius(edgeCoordinates, pointOfDetection,
                                                                                      nearbyEdgePixelScanRadius)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        slope, yOffset = fitLineToCoordinates(edgeCoordinatesInRadiusY, edgeCoordinatesInRadiusX)
    vectorA, vectorB = determineYXorthogonalVectorsForSlope(slope)
    for scanForTransparencyDistance in range(1, maximumScanForTransparencyDistance + 1):
        isDetectionSuccessful, outwardVector = determineOutwardVector(pointOfDetection, vectorA, vectorB, imageArray,
                                                                      scanForTransparencyDistance)
        if isDetectionSuccessful == True:
            break
    outwardAngle = vectorToAngleWithNorthBeingZero(outwardVector)
    return isDetectionSuccessful, outwardAngle, outwardVector


def determineOutwardVector(pointOfDetection, vectorA, vectorB, imageArray, scanForTransparencyDistance):
    scanX_A = pointOfDetection[1] + round(vectorA[1] * scanForTransparencyDistance)
    scanY_A = pointOfDetection[0] + round(vectorA[0] * scanForTransparencyDistance)
    isDetectionSuccessful = True
    isAtowardsTransparency = False
    isBtowardsTransparency = False
    if scanY_A < 0 or scanY_A >= imageArray.shape[0] or scanX_A < 0 or scanX_A >= imageArray.shape[1]:
        isDetectionSuccessful = False
    else:
        isAtowardsTransparency = np.any(imageArray[scanY_A, scanX_A][3] < 255)
    scanX_B = pointOfDetection[1] + round(vectorB[1] * scanForTransparencyDistance)
    scanY_B = pointOfDetection[0] + round(vectorB[0] * scanForTransparencyDistance)
    if scanY_B < 0 or scanY_B >= imageArray.shape[0] or scanX_B < 0 or scanX_B >= imageArray.shape[1]:
        isDetectionSuccessful = False
    else:
        isBtowardsTransparency = np.any(imageArray[scanY_B, scanX_B][3] < 255)

    if isAtowardsTransparency and isBtowardsTransparency:
        isDetectionSuccessful = False
    if not isAtowardsTransparency and not isBtowardsTransparency:
        isDetectionSuccessful = False
    if isAtowardsTransparency:
        outwardVector = vectorA
    else:
        outwardVector = vectorB
    return isDetectionSuccessful, outwardVector


def findEdgePixelsInSearchRadius(edgeCoordinates, pointOfDetection, nearbyEdgePixelScanRadius):
    edgeCoordinatesInRadiusX = []
    edgeCoordinatesInRadiusY = []
    for edgePoint in edgeCoordinates:
        y, x = edgePoint
        yCenter, xCenter = pointOfDetection
        if np.sqrt((xCenter - x) ** 2 + (yCenter - y) ** 2) <= nearbyEdgePixelScanRadius:
            edgeCoordinatesInRadiusX.append(x)
            edgeCoordinatesInRadiusY.append(y)
    return edgeCoordinatesInRadiusY, edgeCoordinatesInRadiusX


def findMeanOfCoordinates(coordinates):
    # TODO: low priority, refactor for performance
    y, x = 0, 0
    for coordinate in coordinates:
        y += coordinate[0]
        x += coordinate[1]
    x = round(x / len(coordinates))
    y = round(y / len(coordinates))
    return y, x


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


def imageDifferenceInPercentage(imageA, imageB):
    differentTransparencyPixels = abs(imageA - imageB)[:, :, 3] > 0
    percentage = 100. * differentTransparencyPixels.sum() / (imageA.shape[0] * imageA.shape[1])
    return percentage


def cropImage(image):
    visiblePixelsY, visiblePixelsX = np.nonzero(image[:, :, 3])
    minX = min(visiblePixelsX)
    maxX = max(visiblePixelsX)
    minY = min(visiblePixelsY)
    maxY = max(visiblePixelsY)
    croppedImage = deepcopy(image[minY:maxY, minX:maxX, :])
    # TODO: consider center of gravity instead?
    center = {}
    center['x'] = (maxX + minX) / 2
    center['y'] = (maxY + minY) / 2
    return croppedImage, center, minX, minY


def shadeImage(imageToShade, colorToIncorporate, weightForColorToIncorporate):
    imageToShadeWithoutAlpha = imageToShade[:, :, 0:3]
    alpha = imageToShade[:, :, 3]
    shadedImage = np.uint8(np.add(np.multiply(1. - weightForColorToIncorporate, imageToShadeWithoutAlpha),
                                            np.multiply(weightForColorToIncorporate, colorToIncorporate)))
    visibleNonBlackCoordinates = np.any(imageToShade != [0, 0, 0, 0], axis=-1)
    red = np.where(visibleNonBlackCoordinates, shadedImage[:, :, 0], imageToShade[:, :, 0])
    green = np.where(visibleNonBlackCoordinates, shadedImage[:, :, 1], imageToShade[:, :, 1])
    blue = np.where(visibleNonBlackCoordinates, shadedImage[:, :, 2], imageToShade[:, :, 2])
    rgba = np.dstack((red, green, blue, alpha))
    return rgba
