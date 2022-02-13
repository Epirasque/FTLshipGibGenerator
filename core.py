import sys
import time

from fileHandling.gibImageSaver import saveGibImages
from fileHandling.shipBlueprintLoader import loadShipFileNames
from fileHandling.shipImageLoader import loadShipBaseImage
from fileHandling.shipLayoutLoader import loadShipLayout
from imageProcessing.segmenter import segment
from metadata.gibEntryChecker import areGibsPresent

MULTIVERSE_FOLDERPATH = 'FTL-Multiverse 5.1 Hotfix'
NR_GIBS = 6


def main(argv):
    start = time.time()
    print("Loading ship file names...")
    ships = loadShipFileNames(MULTIVERSE_FOLDERPATH)
    nrShips = len(ships)
    nrGibsAlreadyPresent = 0
    nrErrorsInMultiverseData = 0
    nrShipsWithGeneratedGibs = 0
    print("Iterating ships...")
    for name, filenames in ships.items():
        shipImageName = filenames['img']
        layoutName = filenames['layout']
        # print('Processing %s ' % name)
        layout = loadShipLayout(layoutName, MULTIVERSE_FOLDERPATH)
        if layout == None:
            print('Cannot process layout for %s ' % name)
            nrErrorsInMultiverseData += 1
        elif areGibsPresent(layout):
            # print('Gibs already present for %s ' % name)
            nrGibsAlreadyPresent += 1
        else:
            baseImg = loadShipBaseImage(shipImageName, MULTIVERSE_FOLDERPATH)
            gibs = segment(baseImg, shipImageName, NR_GIBS)
            saveGibImages(gibs, shipImageName, MULTIVERSE_FOLDERPATH)
            nrShipsWithGeneratedGibs += 1

        break #TODO: remove

    end = time.time()
    print(
        "DONE. Created %u gibs out of %u ships, %u of which had gibs before. Errors when loading multiverse data: %u" % (
        nrShipsWithGeneratedGibs, nrShips, nrGibsAlreadyPresent, nrErrorsInMultiverseData))
    print('Total runtime in minutes: %u' % ((end - start) / 60))


if __name__ == '__main__':
    main(sys.argv)
