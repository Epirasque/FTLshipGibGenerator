import logging

import numpy as np
from skimage.io import imread

from imageProcessing.ImageProcessingUtilities import findColorInImage, findMeanOfCoordinates

logger = logging.getLogger('GLAIVE.' + __name__)

LAYER1 = 'layer1'
DEFAULT_TILESET = 'default/25x21_metal_bit'#'default/10x10_metal_bits_1'
TILE_WIDTH = 25#10  # 72
TILE_HEIGHT = 21#10  # 72
# should divide 360 without remainder
CLOCKWISE_ANGLE_PER_STEP = 45  # 15
NR_ANGLE_STEPS = round(360 / CLOCKWISE_ANGLE_PER_STEP)
NR_ANGLE_STEPS_WHEN_LOADING = round(NR_ANGLE_STEPS / 4)
ORIGIN_COLOR = [0, 255, 0]


def loadTilesets():
    imageArray, tilesetFilePath = loadTilesetFile()
    nrPieces = verifyTilesetDimensions(imageArray, tilesetFilePath)
    tilesets = splitIntoDictionary(imageArray, nrPieces)
    addOriginPixels(tilesets)
    return tilesets


def addOriginPixels(tilesets):
    for piece in tilesets['default'][LAYER1]:
        for angle in range(0, 360, CLOCKWISE_ANGLE_PER_STEP):
            tile = piece[angle]['img']
            coloredArea, coloredCoordinates = findColorInImage(tile, ORIGIN_COLOR)
            originCenterPoint = findMeanOfCoordinates(coloredCoordinates)
            piece[angle]['origin'] = coloredArea, coloredCoordinates, originCenterPoint


def splitIntoDictionary(imageArray, nrPieces):
    tilesets = {}
    tilesets['default'] = {}
    tilesets['default'][LAYER1] = []
    for pieceID in range(nrPieces):
        angleDict = {}
        for angleStep in range(NR_ANGLE_STEPS_WHEN_LOADING):
            yMin = angleStep * TILE_HEIGHT
            yMax = (angleStep + 1) * TILE_HEIGHT  # -1 implicitly given by ':' range
            xMin = pieceID * TILE_WIDTH
            xMax = (pieceID + 1) * TILE_WIDTH  # -1 implicitly given by ':' range
            tile = imageArray[yMin:yMax, xMin:xMax]
            angle = angleStep * CLOCKWISE_ANGLE_PER_STEP
            angleDict[angle] = {}
            angleDict[angle]['img'] = np.ma.copy(tile)
            angleDict[angle + 270] = {}
            angleDict[angle + 270]['img'] = np.rot90(np.ma.copy(angleDict[angle + 0]['img']))
            angleDict[angle + 180] = {}
            angleDict[angle + 180]['img'] = np.rot90(np.ma.copy(angleDict[angle + 270]['img']))
            angleDict[angle + 90] = {}
            angleDict[angle + 90]['img'] = np.rot90(np.ma.copy(angleDict[angle + 180]['img']))

        tilesets['default'][LAYER1].append(angleDict)
    return tilesets


def verifyTilesetDimensions(imageArray, tilesetFilePath):
    ymax, xmax = imageArray.shape[0], imageArray.shape[1]
    if (ymax / TILE_HEIGHT != NR_ANGLE_STEPS_WHEN_LOADING):
        logger.critical('ERROR when reading tileset %s, tileset height does not match expected %u' % (
            tilesetFilePath, TILE_HEIGHT * (360 / CLOCKWISE_ANGLE_PER_STEP)))
        exit(1)
    nrPieces = xmax / TILE_WIDTH
    if nrPieces != round(nrPieces):
        logger.critical(
            'ERROR when reading tileset %s, tileset width is not multiple of %u' % (tilesetFilePath, TILE_WIDTH))
        exit(1)
    return round(nrPieces)


def loadTilesetFile():
    tilesetFilePath = 'metalBits/%s.png' % DEFAULT_TILESET
    imageArray = imread(tilesetFilePath)
    return imageArray, tilesetFilePath
