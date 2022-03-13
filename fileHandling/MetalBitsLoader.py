import imageio
from numpy.ma import copy

from imageProcessing.ImageProcessingUtilities import findColorInImage

LAYER1 = 'chunks'
DEFAULT_TILESET = 'placeholder/rick'
TILE_WIDTH = 72
TILE_HEIGHT = 72
CLOCKWISE_ANGLE_PER_STEP = 15  # should divide 360 without remainder
NR_ANGLE_STEPS = round(360 / CLOCKWISE_ANGLE_PER_STEP)
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
            piece[angle]['originArea'] = coloredArea
            piece[angle]['originCoordinates'] = coloredCoordinates


def splitIntoDictionary(imageArray, nrPieces):
    tilesets = {}
    tilesets['default'] = {}
    tilesets['default'][LAYER1] = []
    for pieceID in range(nrPieces):
        angleDict = {}
        for angleStep in range(NR_ANGLE_STEPS):
            yMin = angleStep * TILE_HEIGHT
            yMax = (angleStep + 1) * TILE_HEIGHT  # -1 implicitly given by ':' range
            xMin = pieceID * TILE_WIDTH
            xMax = (pieceID + 1) * TILE_WIDTH  # -1 implicitly given by ':' range
            tile = imageArray[yMin:yMax, xMin:xMax]
            angle = angleStep * CLOCKWISE_ANGLE_PER_STEP
            angleDict[angle] = {}
            angleDict[angle]['img'] = copy(tile)
        tilesets['default'][LAYER1].append(angleDict)
    return tilesets


def verifyTilesetDimensions(imageArray, tilesetFilePath):
    ymax, xmax = imageArray.shape[0], imageArray.shape[1]
    if (ymax / TILE_HEIGHT != NR_ANGLE_STEPS):
        print('ERROR when reading tileset %s, tileset height does not match expected %u' % (
            tilesetFilePath, TILE_HEIGHT * (360 / CLOCKWISE_ANGLE_PER_STEP)))
        exit(1)
    nrPieces = xmax / TILE_WIDTH
    if nrPieces != round(nrPieces):
        print('ERROR when reading tileset %s, tileset width is not multiple of %u' % (tilesetFilePath, TILE_WIDTH))
        exit(1)
    return round(nrPieces)


def loadTilesetFile():
    tilesetFilePath = '../metalBits/%s.png' % DEFAULT_TILESET
    imageArray = imageio.imread(tilesetFilePath)
    return imageArray, tilesetFilePath
