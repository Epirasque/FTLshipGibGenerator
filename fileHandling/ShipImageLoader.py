import imageio

BASE_SUFFIX = '_base'


def loadShipBaseImage(shipImageName, sourceFolderpath):
    try:
        return imageio.imread(
            sourceFolderpath + '\\img\\ships_glow\\' + shipImageName + BASE_SUFFIX + '.png'), "ships_glow"
    except FileNotFoundError:
        try:
            return imageio.imread(sourceFolderpath + '\\img\\ship\\' + shipImageName + BASE_SUFFIX + '.png'), "ship"
        except FileNotFoundError:
            print('No image found for shipBlueprint img attribute: %s' % shipImageName)
