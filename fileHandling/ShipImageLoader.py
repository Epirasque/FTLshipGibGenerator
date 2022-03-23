import logging

import imageio

logger = logging.getLogger('GLAIVE.' + __name__)


BASE_SUFFIX = '_base'


def loadShipBaseImage(shipImageName, sourceFolderpath):
    try:
        return imageio.imread(
            sourceFolderpath + '\\img\\ships_glow\\' + shipImageName + BASE_SUFFIX + '.png'), "ships_glow"
    except FileNotFoundError:
        try:
            return imageio.imread(sourceFolderpath + '\\img\\ship\\' + shipImageName + BASE_SUFFIX + '.png'), "ship"
        except FileNotFoundError:
            logger.error('No image found for shipBlueprint img attribute: %s' % shipImageName)
