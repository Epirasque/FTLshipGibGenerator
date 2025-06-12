import logging

from skimage.io import imread

from flow.LoggerUtils import getSubProcessLogger
from imageProcessing.GlowRemover import removeGlow

logger = logging.getLogger('GLAIVE.' + __name__)

BASE_SUFFIX = '_base'


def loadShipBaseImage(shipImageName, sourceFolderpath):
    logger = getSubProcessLogger()
    try:
        imageArray = prepareShipImage("ships_glow", shipImageName, sourceFolderpath)
        return imageArray, "ships_glow"
    except FileNotFoundError:
        try:
            imageArray = prepareShipImage("ship", shipImageName, sourceFolderpath)
            return imageArray, "ship"
        except FileNotFoundError:
            try:
                imageArray = prepareShipImage("ships_noglow", shipImageName, sourceFolderpath)
                return imageArray, "ships_noglow"
            except FileNotFoundError:
                logger.error('No image found for shipBlueprint img attribute: %s' % shipImageName)


def prepareShipImage(shipSubfolderName, shipImageName, sourceFolderpath):
    return removeGlow(imread(
        sourceFolderpath + '\\img\\' + shipSubfolderName + '\\' + shipImageName + BASE_SUFFIX + '.png'))
