import sys
import time

from fileHandling.gibImageSaver import saveGibImages
from fileHandling.shipBlueprintLoader import loadShipFileNames
from fileHandling.shipImageLoader import loadShipBaseImage
from fileHandling.shipLayoutDao import loadShipLayout, saveShipLayout
from imageProcessing.segmenter import segment
from metadata.gibEntryAdder import addGitEntriesToLayout
from metadata.gibEntryChecker import areGibsPresent

MULTIVERSE_FOLDERPATH = 'FTL-Multiverse 5.1 Hotfix'
NR_GIBS = 6


def main(argv):
    start = time.time()
    print("Loading ship file names...")
    ships = loadShipFileNames(MULTIVERSE_FOLDERPATH)
    nrShips = len(ships)
    nrShipsWithNewlyGeneratedGibs = 0
    nrShipsWithGibsAlreadyPresent = 0
    nrErrorsInMultiverseData = 0
    nrErrorsInSegmentation = 0
    nrErrorsUnknownCause = 0
    nrIterations = 0
    print("Iterating ships...")
    for name, filenames in ships.items():
        nrIterations += 1
        if (nrIterations % 1) == 0:
            elapsedMinutes = (time.time() - start) / 60.
            finishedFraction = (nrIterations / float(nrShips))
            remainingFraction = 1. - finishedFraction
            remainingMinutes = elapsedMinutes * remainingFraction / finishedFraction
            print(
                "Iterating ships: %u / %u (%.0f%%), elapsed %u minutes, remaining %u minutes), current entry: %s; new: %u, untouched: %u, errors MV: %u, errors SLIC: %u, unknown errors: %u" % (
                    nrIterations, nrShips, 100. * finishedFraction, elapsedMinutes, remainingMinutes, name,
                    nrShipsWithNewlyGeneratedGibs, nrShipsWithGibsAlreadyPresent, nrErrorsInMultiverseData,
                    nrErrorsInSegmentation, nrErrorsUnknownCause))
        shipImageName = filenames['img']
        layoutName = filenames['layout']
        # print('Processing %s ' % name)
        layout = loadShipLayout(layoutName, MULTIVERSE_FOLDERPATH)
        if layout == None:
            print('Cannot process layout for %s ' % name)
            nrErrorsInMultiverseData += 1
        elif areGibsPresent(layout):
            # print('Gibs already present for %s ' % name)
            nrShipsWithGibsAlreadyPresent += 1
        else:
            try:
                baseImg, shipImageSubfolder = loadShipBaseImage(shipImageName, MULTIVERSE_FOLDERPATH)
                gibs = segment(baseImg, shipImageName, NR_GIBS)
                if len(gibs) == 0:
                    nrErrorsInSegmentation += 1
                else:
                    saveGibImages(gibs, shipImageName, shipImageSubfolder, MULTIVERSE_FOLDERPATH)
                    layoutWithNewGibs = addGitEntriesToLayout(layout, gibs)
                    saveShipLayout(layoutWithNewGibs, layoutName, MULTIVERSE_FOLDERPATH)
                    # print("Done with %s " % name)
                    nrShipsWithNewlyGeneratedGibs += 1
            except Exception as e:
                print(e)
                nrErrorsUnknownCause += 1

        # break  # TODO: remove

    end = time.time()
    print(
        "DONE. Created %u gibs out of %u ships, %u of which had gibs before. \nErrors when loading multiverse data: %u. Failed ship segmentations: %u. Unknown errors: %u" % (
            nrShipsWithNewlyGeneratedGibs, nrShips, nrShipsWithGibsAlreadyPresent, nrErrorsInMultiverseData,
            nrErrorsInSegmentation, nrErrorsUnknownCause))
    print('Total runtime in minutes: %u' % ((end - start) / 60))


if __name__ == '__main__':
    main(sys.argv)
