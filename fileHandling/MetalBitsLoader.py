import logging
import os
import random
import statistics

import numpy as np
from matplotlib import pyplot as plt
from skimage.io import imread

from imageProcessing.ImageProcessingUtilities import determineOutwardDirectionAtPoint, findColorInImage, \
    findMeanOfCoordinates
from imageProcessing.MetalBitsConstants import TILESET_ATTACHMENT_EDGE_COLOR, TILESET_PROCESSED_ATTACHMENT_EDGE_COLOR

logger = logging.getLogger('GLAIVE.' + __name__)

LAYER1 = 'layer1'
LAYER3 = 'layer3'
# always end with trailing / here
FOLDER_NAME = "metalBits/"
NR_FILENAME_ENCODED_PARAMETERS = 2
# is applied in both directions
LAYER1_ANGLE_TOLERANCE_SPREAD_FOR_TILE_RANDOM_SELECTION = 15
LAYER3_ANGLE_TOLERANCE_SPREAD_FOR_TILE_RANDOM_SELECTION = 40


def loadTilesets():
    tilesetFilepaths = determineTilesetFilepaths(FOLDER_NAME)
    tilesets = loadTilesetsIntoDictionary(FOLDER_NAME, tilesetFilepaths)
    return tilesets


def determineTilesetFilepaths(folderName):
    filenames = []
    for file in os.listdir(folderName):
        if file.lower().endswith(".png") and file.startswith('layer'):
            filenames.append(file)
            logger.info('Detected %s' % file)
        else:
            logger.warning('Unexpected file in %s: %s' % (folderName, file))
    return filenames


def loadTilesetsIntoDictionary(folderName, tilesetFilepaths):
    tilesets = {}
    for tilesetFilepath in tilesetFilepaths:
        loadSingleTilesetIntoDictionary(folderName, tilesetFilepath, tilesets)

    distributeTilesToAngles(tilesets, LAYER1, LAYER1_ANGLE_TOLERANCE_SPREAD_FOR_TILE_RANDOM_SELECTION)
    distributeTilesToAngles(tilesets, LAYER3, LAYER3_ANGLE_TOLERANCE_SPREAD_FOR_TILE_RANDOM_SELECTION)
    return tilesets


def distributeTilesToAngles(tilesets, layerName, angleTolerance):
    layerDistribution = []
    layerDistributionString = ''
    angleRange = range(90)
    for angle in angleRange:
        layerDistribution.append(len(tilesets[layerName][angle]))
        layerDistributionString += "%s, for angle %2u: %u tiles\n" % (layerName, angle, len(tilesets[layerName][angle]))
    logger.info('Tile distribution for %s (including tolerance of %u): \n%s' % (layerName,
                                                                                angleTolerance,
                                                                                layerDistributionString))
    if min(layerDistribution) == 0:
        logger.critical(
            'For %s, at least one angle has no valid tile to choose from: %s' % (layerName, layerDistribution))
    plt.figure(1)
    plt.bar(angleRange, np.asarray(layerDistribution))
    plt.title(
        '%s: nr. of available tiles for each angle (including tolerance of %u)' % (layerName, angleTolerance))
    plt.savefig('%s_tiles_per_angle.png' % layerName)
    plt.figure(2)
    plt.hist(layerDistribution)
    plt.title(
        '%s: histogram of tile-amount-occurrences (including tolerance of %u)' % (layerName, angleTolerance))
    plt.savefig('%s_tile_histogram.png' % layerName)


def loadSingleTilesetIntoDictionary(folderName, tilesetFilepath, tilesets):
    layer, tilesetDimension = parseFilenameParameters(tilesetFilepath)
    validLayer = False
    rotationTolerance = 0
    if layer == LAYER1:
        validLayer = True
        rotationTolerance = LAYER1_ANGLE_TOLERANCE_SPREAD_FOR_TILE_RANDOM_SELECTION
    elif layer == LAYER3:
        validLayer = True
        rotationTolerance = LAYER3_ANGLE_TOLERANCE_SPREAD_FOR_TILE_RANDOM_SELECTION
    if validLayer == True:
        initializeLayerInDictionary(layer, tilesets)
        imageArray = imread(folderName + tilesetFilepath)
        ymax = determineFileDimensions(imageArray, tilesetDimension, tilesetFilepath)
        nrTiles = determineNrOfTiles(tilesetDimension, tilesetFilepath, ymax)
        for tileId in range(nrTiles):
            addTileWithIDToDictionary(imageArray, layer, rotationTolerance, nrTiles, tileId, tilesetDimension,
                                      tilesetFilepath, tilesets)


def addTileWithIDToDictionary(imageArray, layer, rotationTolerance, nrTiles, tileId, tilesetDimension, tilesetFilepath,
                              tilesets):
    tile = extractTileArray(imageArray, tileId, tilesetDimension)
    tile0turned = np.ma.copy(tile)
    remainingUncoveredAttachmentEdgePixels = np.where(
        np.all(tile == TILESET_ATTACHMENT_EDGE_COLOR, axis=-1))
    allEdgePixelsAsList, initialNrAttachmentEdgePixels = determineAllInitialEdgePixelsAsList(
        remainingUncoveredAttachmentEdgePixels)
    determinedOrientations, nrFailedOrientationDetections, nrSuccessfulOrientationDetections = determineOrientationsForEdge(
        allEdgePixelsAsList, remainingUncoveredAttachmentEdgePixels, tile, tilesetDimension)
    successRate = determineSuccessRate(nrFailedOrientationDetections, nrSuccessfulOrientationDetections, tileId,
                                       tilesetFilepath)
    medianOrientation = consolidateOrientationsIntoSingleOrientation(determinedOrientations)
    medianOrientationInFirstQuadrant = medianOrientation % 90
    standardDeviationForOrientation = determineStandardDeviation(determinedOrientations)
    logger.debug(
        '%s: Determined tile nr %u / %u in %s with %u%% orientation detection rate for %u attachment pixels, median orientation: %u, median rotation as in first quadrant: %u, (standard deviation: %.2f), orientatinos: %s' %
        (layer, tileId + 1, nrTiles, tilesetFilepath, successRate, initialNrAttachmentEdgePixels, medianOrientation,
         medianOrientationInFirstQuadrant, standardDeviationForOrientation, determinedOrientations))
    # has processed attachment edge color
    del tile
    if medianOrientation >= 270:
        tile0turned = np.rot90(np.ma.copy(tile0turned))
    if medianOrientation >= 180:
        tile0turned = np.rot90(np.ma.copy(tile0turned))
    if medianOrientation >= 90:
        tile0turned = np.rot90(np.ma.copy(tile0turned))
    # original tile does not have to be between 0° and 90° for this to work
    tile270turned = np.rot90(np.ma.copy(tile0turned))
    tile180turned = np.rot90(np.ma.copy(tile270turned))
    tile90turned = np.rot90(np.ma.copy(tile180turned))
    for angleWithinTolerance in range(
            medianOrientationInFirstQuadrant - rotationTolerance,
            medianOrientationInFirstQuadrant + rotationTolerance + 1):
        allowTileToCoverAngle(angleWithinTolerance, layer, tile0turned, tile180turned, tile270turned, tile90turned,
                              tilesets)


def allowTileToCoverAngle(angleWithinTolerance, layer, tile0turned, tile180turned, tile270turned, tile90turned,
                          tilesets):
    coveredAngle = angleWithinTolerance % 360
    addTileToTileset(coveredAngle, layer, tile0turned, tilesets)
    coveredAngle = (coveredAngle + 90) % 360
    addTileToTileset(coveredAngle, layer, tile90turned, tilesets)
    coveredAngle = (coveredAngle + 90) % 360
    addTileToTileset(coveredAngle, layer, tile180turned, tilesets)
    coveredAngle = (coveredAngle + 90) % 360
    addTileToTileset(coveredAngle, layer, tile270turned, tilesets)


def addTileToTileset(coveredAngle, layer, tile, tilesets):
    angleDict = {}
    angleDict['img'] = tile
    coloredArea, coloredCoordinates = findColorInImage(tile, TILESET_ATTACHMENT_EDGE_COLOR)
    originCenterPoint = findMeanOfCoordinates(coloredCoordinates)
    angleDict['origin'] = coloredArea, coloredCoordinates, originCenterPoint
    tilesets[layer][coveredAngle].append(angleDict)


def determineStandardDeviation(determinedOrientations):
    standardDeviationForOrientation = np.std(determinedOrientations)
    if standardDeviationForOrientation > 0.:
        logger.warning(
            "standard deviation for orientation detection is above 0: %.2f" % standardDeviationForOrientation)
    return standardDeviationForOrientation


def consolidateOrientationsIntoSingleOrientation(determinedOrientations):
    return int(round(statistics.median(determinedOrientations)))


def determineSuccessRate(nrFailedOrientationDetections, nrSuccessfulOrientationDetections, tileId, tilesetFilepath):
    if nrFailedOrientationDetections > 0:
        successRate = round(nrSuccessfulOrientationDetections * 100 / (
                nrSuccessfulOrientationDetections + nrFailedOrientationDetections))
    else:
        successRate = 100
    if nrSuccessfulOrientationDetections == 0:
        raise Exception('tile nr %u in %s: failed to detect orientation for even one edge pixel' % (
            tileId, tilesetFilepath))
    return successRate


def determineOrientationsForEdge(allEdgePixelsAsList, remainingUncoveredAttachmentEdgePixels, tile, tilesetDimension):
    nrSuccessfulOrientationDetections = 0
    nrFailedOrientationDetections = 0
    determinedOrientations = []
    while np.any(remainingUncoveredAttachmentEdgePixels):
        attachmentPointId = random.randint(0, len(remainingUncoveredAttachmentEdgePixels[0]) - 1)
        edgePointToCheck = remainingUncoveredAttachmentEdgePixels[0][attachmentPointId], \
                           remainingUncoveredAttachmentEdgePixels[1][
                               attachmentPointId]

        isDetectionSuccessful, outwardAngle, outwardVectorYX = determineOutwardDirectionAtPoint(
            tile,
            allEdgePixelsAsList,
            edgePointToCheck,
            tilesetDimension,
            tilesetDimension)

        tile[edgePointToCheck] = TILESET_PROCESSED_ATTACHMENT_EDGE_COLOR
        remainingUncoveredAttachmentEdgePixels = np.where(
            np.all(tile == TILESET_ATTACHMENT_EDGE_COLOR, axis=-1))

        if isDetectionSuccessful:
            nrSuccessfulOrientationDetections += 1
            outwardAngle = (
                                   outwardAngle + 180) % 360  # invert since we want to attach the tile and not ONTO the tile
            determinedOrientations.append(outwardAngle)
        else:
            nrFailedOrientationDetections += 1
    return determinedOrientations, nrFailedOrientationDetections, nrSuccessfulOrientationDetections


def determineAllInitialEdgePixelsAsList(remainingUncoveredAttachmentEdgePixels):
    initialNrAttachmentEdgePixels = remainingUncoveredAttachmentEdgePixels[0].size
    allEdgePixelsAsList = []
    for edgePixelId in range(initialNrAttachmentEdgePixels):
        allEdgePixelsAsList.append((remainingUncoveredAttachmentEdgePixels[0][edgePixelId],
                                    remainingUncoveredAttachmentEdgePixels[1][edgePixelId]))
    return allEdgePixelsAsList, initialNrAttachmentEdgePixels


def extractTileArray(imageArray, tileId, tilesetDimension):
    xMin = 0
    xMax = tilesetDimension
    yMin = tileId * tilesetDimension
    yMax = (tileId + 1) * tilesetDimension  # -1 implicitly given by ':' range
    tile = imageArray[yMin:yMax, xMin:xMax]
    return tile


def determineNrOfTiles(tilesetDimension, tilesetFilepath, ymax):
    nrTiles = float(ymax) / tilesetDimension
    if nrTiles != round(nrTiles):
        raise Exception(
            "Tileset height is supposed to be an integer multiple of %u pixels but is actually a multiple of %f.2f: %s" % (
                tilesetDimension, nrTiles, tilesetFilepath))
    nrTiles = int(nrTiles)
    return nrTiles


def determineFileDimensions(imageArray, tilesetDimension, tilesetFilepath):
    ymax, xmax = imageArray.shape[0], imageArray.shape[1]
    if xmax != tilesetDimension:
        raise Exception("Tileset width is supposed to be %u pixels but is actually %u: %s" % (
            tilesetDimension, xmax, tilesetFilepath))
    return ymax


def initializeLayerInDictionary(layer, tilesets):
    if not layer in tilesets:
        tilesets[layer] = {}
        for coveredAngle in range(360):
            tilesets[layer][coveredAngle] = []


def parseFilenameParameters(tilesetFilepath):
    filenameParameters = tilesetFilepath.split('_')
    if len(filenameParameters) != NR_FILENAME_ENCODED_PARAMETERS:
        raise Exception('Malformed filename, expected %u parameters separated by _: %s' % (
            NR_FILENAME_ENCODED_PARAMETERS, tilesetFilepath))
    try:
        layer = filenameParameters[0]
        tilesetDimension = int(filenameParameters[1].split('x')[0])
    except Exception as e:
        raise Exception("Failed to decode filename parameters for %s: %s" % (tilesetFilepath, e))
    return layer, tilesetDimension
