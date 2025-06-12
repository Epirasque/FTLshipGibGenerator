import configparser
import sys
from copy import deepcopy

import imageio
import numpy as np
from PIL import Image

from fileHandling.ShipBlueprintLoader import loadShipFileNames
from skimage.io import imread

from fileHandling.ShipImageLoader import BASE_SUFFIX
from imageProcessing.GlowRemover import removeGlow


def main(argv):
    configParser = configparser.ConfigParser()
    configParser.read('config.ini')
    coreConfig = configParser['core']
    INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH = coreConfig.get('INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH',
                                                            fallback='FTL-Multiverse 5.x')
    ships_to_ignore_raw_string = coreConfig.get('SHIPS_TO_IGNORE',
                                                fallback='PLAYER_SHIP_TUTORIAL, MU_COALITION_CONSTRUCTION')
    SHIPS_TO_IGNORE = ships_to_ignore_raw_string.replace(' ', '').split(',')
    CHECK_SPECIFIC_SHIPS = coreConfig.getboolean('CHECK_SPECIFIC_SHIPS', fallback=False)
    specific_ship_names_raw_string = coreConfig.get('SPECIFIC_SHIP_NAMES', fallback='')
    SPECIFIC_SHIP_NAMES = specific_ship_names_raw_string.replace(' ', '').split(',')

    ships, layoutUsages = loadShipFileNames(INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH)

    nrTransparentShips = 0
    for shipName, shipMetadata in ships.items():
        if CHECK_SPECIFIC_SHIPS == True:
            if shipName not in SPECIFIC_SHIP_NAMES:
                # logger.debug("Skipping %s (not in whitelist)" % shipName)
                continue
        if shipName in SHIPS_TO_IGNORE:
            print("Skipping %s (is in blacklist)" % shipName)
            continue

        shipImageName = shipMetadata['img']
        try:
            imageArray = imread(
                INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH + '\\img\\' + "ships_glow" + '\\' + shipImageName + BASE_SUFFIX + '.png')
        except:
            try:
                imageArray = imread(
                    INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH + '\\img\\' + "ship" + '\\' + shipImageName + BASE_SUFFIX + '.png')
            except:
                try:
                    imageArray = imread(
                        INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH + '\\img\\' + "ships_noglow" + '\\' + shipImageName + BASE_SUFFIX + '.png')
                except FileNotFoundError:
                    print('ERROR: No image found for shipBlueprint img attribute: %s' % shipImageName)
        # remove fully visible pixels
        originalImageArray = deepcopy(imageArray)
        imageArray = removeGlow(imageArray)
        #imageArray[imageArray[:, :, 3] == 255] = 0

        partiallyTransparentPoints = np.where((imageArray[:, :, 3] >= 1) & (imageArray[:, :, 3] < 255))
        if(partiallyTransparentPoints[0].size > 0):
            print(f'{shipImageName} : {partiallyTransparentPoints[0].size}')
            nrTransparentShips += 1

            imageArray[partiallyTransparentPoints] = [255, 0, 0, 255]
            imageio.imwrite('transparent_ships\\' + str(partiallyTransparentPoints[0].size) + '_NONGLOW_PIXELS_IN_' + shipImageName + '.png', imageArray)
            originalImageArray[partiallyTransparentPoints[0], partiallyTransparentPoints[1], 3] = 255
            imageio.imwrite('ships_made_nontransparent\\' + shipImageName + '_base.png', originalImageArray)
            #pass
    print('partially transparent ships: %u' % nrTransparentShips)

if __name__ == '__main__':
    main(sys.argv)
