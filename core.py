import sys
import time

from fileHandling.shipBlueprintLoader import loadShipFileNames
from fileHandling.shipImageLoader import loadShipBaseImage
from fileHandling.shipMetadataLoader import loadShipMetadata
from metadata.gibEntryChecker import areGibsPresent

MULTIVERSE_FOLDERPATH = 'FTL-Multiverse 5.1 Hotfix'

def main(argv):
    start = time.time()
    print("Loading ship file names...")
    ships = loadShipFileNames(MULTIVERSE_FOLDERPATH)
    nrShips = len(ships)
    nrGibsAlreadyPresent = 0
    nrErrorsInMultiverseData = 0
    print("Iterating ships...")
    for name, filenames in ships.items():
        #print('Processing %s ' % name)
        layout = loadShipMetadata(filenames['layout'], MULTIVERSE_FOLDERPATH)
        if layout == None:
            print('Cannot process layout for %s ' % name)
            nrErrorsInMultiverseData += 1
        elif areGibsPresent(layout):
            #print('Gibs already present for %s ' % name)
            nrGibsAlreadyPresent += 1
        else:
            baseImg = loadShipBaseImage(filenames['img'], MULTIVERSE_FOLDERPATH)
        #break #TODO: remove

    end = time.time()
    print("DONE. Created %u gibs out of %u ships, %u of which had gibs before. Errors when loading multiverse data: %u" % (0, nrShips, nrGibsAlreadyPresent, nrErrorsInMultiverseData))
    print('Total runtime in minutes: %u' % ((end-start)/60))

if __name__ == '__main__':
    main(sys.argv)

