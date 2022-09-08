import logging

import numpy as np
from skimage.io import imread

from flow.LoggerUtils import getSubProcessLogger

logger = logging.getLogger('GLAIVE.' + __name__)

BASE_SUFFIX = '_base'

VISIBLE_ALPHA_THRESHOLD = 255


def loadShipBaseImage(shipImageName, sourceFolderpath):
    logger = getSubProcessLogger()
    try:
        imageArray = prepareShipImage("ship_glow", shipImageName, sourceFolderpath)
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
    imageArray = imread(
        sourceFolderpath + '\\img\\' + shipSubfolderName + '\\' + shipImageName + BASE_SUFFIX + '.png')
    # glow should be ignored, is treated as completely transparent
    imageArray[imageArray[:, :, 3] < VISIBLE_ALPHA_THRESHOLD] = 0
    # only overwrite alpha, not the colors
    visiblePoints = np.where(imageArray[:, :, 3] >= VISIBLE_ALPHA_THRESHOLD)
    imageArray[visiblePoints[0], visiblePoints[1], 3] = 255
    return imageArray
