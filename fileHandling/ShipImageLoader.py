import logging

import numpy as np
from skimage.io import imread

from flow.LoggerUtils import getSubProcessLogger

logger = logging.getLogger('GLAIVE.' + __name__)

BASE_SUFFIX = '_base'

VISIBLE_ALPHA_THRESHOLD = 64


def loadShipBaseImage(shipImageName, sourceFolderpath):
    logger = getSubProcessLogger()
    try:
        imageArray = imread(
            sourceFolderpath + '\\img\\ships_glow\\' + shipImageName + BASE_SUFFIX + '.png')
        # glow should be ignored, is treated as completely transparent
        imageArray[imageArray[:, :, 3] < VISIBLE_ALPHA_THRESHOLD] = 0
        # only overwrite alpha, not the colors
        visiblePoints = np.where(imageArray[:, :, 3] >= VISIBLE_ALPHA_THRESHOLD)
        imageArray[visiblePoints[0], visiblePoints[1], 3] = 255
        return imageArray, "ships_glow"
    except FileNotFoundError:
        try:
            imageArray = imread(
                sourceFolderpath + '\\img\\ship\\' + shipImageName + BASE_SUFFIX + '.png')
            # glow should be ignored, is treated as completely transparent
            imageArray[imageArray[:, :, 3] < VISIBLE_ALPHA_THRESHOLD] = 0
            # only overwrite alpha, not the colors
            visiblePoints = np.where(imageArray[:, :, 3] >= VISIBLE_ALPHA_THRESHOLD)
            imageArray[visiblePoints[0], visiblePoints[1], 3] = 255
            return imageArray, "ship"
        except FileNotFoundError:
            logger.error('No image found for shipBlueprint img attribute: %s' % shipImageName)
