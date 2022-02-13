import imageio

BASE_SUFFIX = '_base'


def loadShipBaseImage(shipImageName, multiverseFolderpath):
    try:
        return imageio.imread(
            multiverseFolderpath + '\\img\\ships_glow\\' + shipImageName + BASE_SUFFIX + '.png'), "ships_glow"
    except FileNotFoundError:
        try:
            return imageio.imread(multiverseFolderpath + '\\img\\ship\\' + shipImageName + BASE_SUFFIX + '.png'), "ship"
        except FileNotFoundError:
            print('No image found for shipBlueprint img attribute: %s' % shipImageName)
