import imageio

BASE_SUFFIX = '_base'


def loadShipBaseImage(shipImageName, multiverseFolderpath):
    try:
        return imageio.imread(multiverseFolderpath + '\\img\\ships_glow\\' + shipImageName + BASE_SUFFIX + '.png')
    except FileNotFoundError:
        try: #TODO: refactor to ensure gibs are placed next to base image (or assume all player ships have gibs)
            return imageio.imread(multiverseFolderpath + '\\img\\ship\\' + shipImageName + BASE_SUFFIX + '.png')
        except FileNotFoundError:
            print('No image found for shipBlueprint img attribute: %s' % shipImageName)
