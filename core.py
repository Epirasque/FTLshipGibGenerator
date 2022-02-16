import sys
import time

from fileHandling.gibImageChecker import areGibsPresentAsImageFiles
from fileHandling.gibImageSaver import saveGibImagesStandalone
from fileHandling.shipBlueprintLoader import loadShipFileNames
from fileHandling.shipImageLoader import loadShipBaseImage
from fileHandling.shipLayoutDao import loadShipLayout, saveShipLayoutStandalone, saveShipLayoutAsAppendFile
from imageProcessing.segmenter import segment
from metadata.gibEntryAdder import addGibEntriesToLayout
from metadata.gibEntryChecker import areGibsPresentInLayout
from metadata.layoutToAppendContentConverter import convertLayoutToAppendContent

MULTIVERSE_FOLDERPATH = 'FTL-Multiverse 5.1 Hotfix'
ADDON_FOLDERPATH = 'addon'
NR_GIBS = 2

QUICK_AND_DIRTY_SEGMENT = True
CHECK_SPECIFIC_SHIP = False
SPECIFIC_SHIP_NAME = 'MU_ORCHID_FIGHTER'
LIMIT_ITERATIONS = True
ITERATION_LIMIT = 10

BACKUP_SEGMENTS_FOR_DEVELOPER = False
BACKUP_LAYOUTS_FOR_DEVELOPER = True


def main(argv):
    globalStart = time.time()
    print("Loading ship file names...")
    ships = loadShipFileNames(MULTIVERSE_FOLDERPATH)
    nrShips = len(ships)
    nrShipsWithNewlyGeneratedGibs = 0
    nrShipsWithGibsAlreadyPresent = 0
    nrShipsWithIncompleteGibSetup = 0
    nrErrorsInMultiverseData = 0
    nrErrorsInSegmentation = 0
    nrErrorsUnknownCause = 0
    nrIterations = 0
    totalLoadShipBaseImageDuration = 0
    totalSegmentDuration = 0
    totalSaveGibImagesDuration = 0
    totalAddGibEntriesToLayoutDuration = 0
    totalSaveShipLayoutDuration = 0
    print("Iterating ships... (nr gibs per ship: %u)" % NR_GIBS)
    for name, filenames in ships.items():
        if CHECK_SPECIFIC_SHIP == True:
            if name != SPECIFIC_SHIP_NAME:
                continue
        nrIterations += 1
        printIterationInfo(globalStart, name, nrErrorsInMultiverseData, nrErrorsInSegmentation, nrErrorsUnknownCause,
                           nrIterations, nrShips, nrShipsWithGibsAlreadyPresent, nrShipsWithNewlyGeneratedGibs,
                           nrShipsWithIncompleteGibSetup, totalAddGibEntriesToLayoutDuration,
                           totalLoadShipBaseImageDuration, totalSaveGibImagesDuration, totalSaveShipLayoutDuration,
                           totalSegmentDuration)
        shipImageName = filenames['img']
        layoutName = filenames['layout']

        # print('Processing %s ' % name)
        layout = loadShipLayout(layoutName, MULTIVERSE_FOLDERPATH)
        if layout == None:
            print('Cannot process layout for %s ' % name)
            nrErrorsInMultiverseData += 1
        elif areGibsPresentInLayout(layout) and areGibsPresentAsImageFiles(shipImageName, MULTIVERSE_FOLDERPATH):
            # print('Gibs already present for %s ' % name)
            nrShipsWithGibsAlreadyPresent += 1
        else:
            if areGibsPresentInLayout(layout) or areGibsPresentAsImageFiles(shipImageName, MULTIVERSE_FOLDERPATH):
                nrShipsWithIncompleteGibSetup += 1
            try:
                baseImg, shipImageSubfolder, totalLoadShipBaseImageDuration = loadShipBaseImageWithProfiling(
                    shipImageName, totalLoadShipBaseImageDuration)
                gibs, totalSegmentDuration = segmentWithProfiling(baseImg, shipImageName, totalSegmentDuration)
                if len(gibs) == 0:
                    nrErrorsInSegmentation += 1
                else:
                    totalSaveGibImagesDuration = saveGibImagesWithProfiling(gibs, shipImageName, shipImageSubfolder,
                                                                            totalSaveGibImagesDuration)
                    layoutWithNewGibs, appendContentString, totalAddGibEntriesToLayoutDuration = addGibEntriesToLayoutWithProfiling(
                        gibs,
                        layout,
                        totalAddGibEntriesToLayoutDuration)
                    totalSaveShipLayoutDuration = saveShipLayoutWithProfiling(layoutName, layoutWithNewGibs,
                                                                              appendContentString,
                                                                              totalSaveShipLayoutDuration)
                    # print("Done with %s " % name)
                    nrShipsWithNewlyGeneratedGibs += 1
            except Exception as e:
                print("UNEXPECTED EXCEPTION: %s" % e)
                nrErrorsUnknownCause += 1

        if LIMIT_ITERATIONS == True and nrIterations >= ITERATION_LIMIT:
            break

    print(
        "DONE. Created gibs for %u ships out of %u ships, %u of which had gibs before, %u of which had an incomplete gib setup. \nErrors when loading multiverse data: %u. Failed ship segmentations: %u. Unknown errors: %u" % (
            nrShipsWithNewlyGeneratedGibs, nrShips, nrShipsWithGibsAlreadyPresent, nrShipsWithIncompleteGibSetup,
            nrErrorsInMultiverseData,
            nrErrorsInSegmentation, nrErrorsUnknownCause))
    print('Total runtime in minutes: %u' % ((time.time() - globalStart) / 60))


def saveShipLayoutWithProfiling(layoutName, layoutWithNewGibs, appendContentString, totalSaveShipLayoutDuration):
    start = time.time()
    saveShipLayoutStandalone(layoutWithNewGibs, layoutName, MULTIVERSE_FOLDERPATH,
                             developerBackup=BACKUP_LAYOUTS_FOR_DEVELOPER)
    saveShipLayoutAsAppendFile(appendContentString, layoutName, ADDON_FOLDERPATH,
                               developerBackup=BACKUP_LAYOUTS_FOR_DEVELOPER)
    totalSaveShipLayoutDuration += time.time() - start
    return totalSaveShipLayoutDuration


def addGibEntriesToLayoutWithProfiling(gibs, layout, totalAddGibEntriesToLayoutDuration):
    start = time.time()
    layoutWithNewGibs = addGibEntriesToLayout(layout, gibs)
    appendContentString = convertLayoutToAppendContent(layoutWithNewGibs)
    totalAddGibEntriesToLayoutDuration += time.time() - start
    return layoutWithNewGibs, appendContentString, totalAddGibEntriesToLayoutDuration


def saveGibImagesWithProfiling(gibs, shipImageName, shipImageSubfolder, totalSaveGibImagesDuration):
    start = time.time()
    saveGibImagesStandalone(gibs, shipImageName, shipImageSubfolder, MULTIVERSE_FOLDERPATH,
                            developerBackup=BACKUP_SEGMENTS_FOR_DEVELOPER)
    totalSaveGibImagesDuration += time.time() - start
    return totalSaveGibImagesDuration


def segmentWithProfiling(baseImg, shipImageName, totalSegmentDuration):
    start = time.time()
    gibs = segment(baseImg, shipImageName, NR_GIBS, QUICK_AND_DIRTY_SEGMENT)
    totalSegmentDuration += time.time() - start
    return gibs, totalSegmentDuration


def loadShipBaseImageWithProfiling(shipImageName, totalLoadShipBaseImageDuration):
    start = time.time()
    baseImg, shipImageSubfolder = loadShipBaseImage(shipImageName, MULTIVERSE_FOLDERPATH)
    totalLoadShipBaseImageDuration += time.time() - start
    return baseImg, shipImageSubfolder, totalLoadShipBaseImageDuration


def printIterationInfo(globalStart, name, nrErrorsInMultiverseData, nrErrorsInSegmentation, nrErrorsUnknownCause,
                       nrIterations, nrShips, nrShipsWithGibsAlreadyPresent, nrShipsWithNewlyGeneratedGibs,
                       nrShipsWithIncompleteGibSetup, totalAddGibEntriesToLayoutDuration,
                       totalLoadShipBaseImageDuration, totalSaveGibImagesDuration,
                       totalSaveShipLayoutDuration, totalSegmentDuration):
    if (nrIterations % 1) == 0:
        elapsedMinutes = (time.time() - globalStart) / 60.
        finishedFraction = (nrIterations / float(nrShips))
        remainingFraction = 1. - finishedFraction
        remainingMinutes = elapsedMinutes * remainingFraction / finishedFraction
        print(
            "Iterating ships: %u / %u (%.0f%%), elapsed %u minutes, remaining %u minutes, current entry: %s; new: %u, untouched: %u, incomplete in MV: %u, errors MV: %u, errors SLIC: %u, unknown errors: %u" % (
                nrIterations, nrShips, 100. * finishedFraction, elapsedMinutes, remainingMinutes, name,
                nrShipsWithNewlyGeneratedGibs, nrShipsWithGibsAlreadyPresent, nrShipsWithIncompleteGibSetup,
                nrErrorsInMultiverseData,
                nrErrorsInSegmentation, nrErrorsUnknownCause))
    if (nrIterations % 5) == 0:  # note that this is BEFORE the current iteration has finished!
        totalDuration = totalLoadShipBaseImageDuration + totalSegmentDuration + totalSaveGibImagesDuration + totalAddGibEntriesToLayoutDuration + totalSaveShipLayoutDuration
        if totalDuration > 0:
            totalLoadShipBaseImagePercentage = round(100 * totalLoadShipBaseImageDuration / totalDuration)
            totalSegmentDurationPercentage = round(100 * totalSegmentDuration / totalDuration)
            totalSaveGibImagesDurationPercentage = round(100 * totalSaveGibImagesDuration / totalDuration)
            totalAddGibEntriesToLayoutDurationPercentage = round(
                100 * totalAddGibEntriesToLayoutDuration / totalDuration)
            totalSaveShipLayoutDurationPercentage = round(100 * totalSaveShipLayoutDuration / totalDuration)
            print(
                "PROFILING: average profiled duration per iteration: %.3f seconds, loadShipBaseImage: %u%%, segment: %u%%, saveGibImages: %u%%, addGibEntriesToLayout: %u%%, saveShipLayout: %u%%" % (
                    (totalDuration / (nrIterations - 1.)), totalLoadShipBaseImagePercentage,
                    totalSegmentDurationPercentage,
                    totalSaveGibImagesDurationPercentage, totalAddGibEntriesToLayoutDurationPercentage,
                    totalSaveShipLayoutDurationPercentage))


if __name__ == '__main__':
    main(sys.argv)
