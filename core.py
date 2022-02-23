import sys
import time

from fileHandling.gibImageChecker import areGibsPresentAsImageFiles
from fileHandling.gibImageSaver import saveGibImages
from fileHandling.shipBlueprintLoader import loadShipFileNames
from fileHandling.shipImageLoader import loadShipBaseImage
from fileHandling.shipLayoutDao import loadShipLayout, saveShipLayoutStandalone, saveShipLayoutAsAppendFile
from imageProcessing.segmenter import segment
from metadata.gibEntryAdder import addGibEntriesToLayout
from metadata.gibEntryChecker import areGibsPresentInLayout
from metadata.layoutToAppendContentConverter import convertLayoutToAppendContent
from metadata.weaponMountGibIdUpdater import setWeaponMountGibIdsAsAppendContent

# Source for metadata semantics: https://www.ftlwiki.com/wiki/Modding_ships

# note: use / instead of \ to avoid character-escaping issues
INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH = 'C:/Users/roman/PycharmProjects/glaive/AllEnemyShipsPlayable v1.3'  # 'FTL-Multiverse 5.1 Hotfix'
ADDON_OUTPUT_FOLDERPATH = 'not needed for standalone...'  # e.g. 'MV Addon GenGibs v0.9'
# tutorial is part of vanilla and should have gibs. MU_COALITION_CONSTRUCTION seems to be a bug in MV, has no layout file
SHIPS_TO_IGNORE = ['PLAYER_SHIP_TUTORIAL', 'MU_COALITION_CONSTRUCTION']
# configure whether the output is meant for standalone or as an addon.
# KEEP A BACKUP READY! it is best practice to restore the backup before generating new gibs, .bat files can help a lot for that
SAVE_STANDALONE = True
SAVE_ADDON = False
# if enabled, save a separate copy of the output in gibs and/or layouts folders; these are NOT cleaned up automatically
BACKUP_STANDALONE_SEGMENTS_FOR_DEVELOPER = False
BACKUP_STANDALONE_LAYOUTS_FOR_DEVELOPER = False

# actual number can be less: if the algorithm has an issue it is retried with fewer gibs
NR_GIBS = 5
# enable for sanity checks
QUICK_AND_DIRTY_SEGMENT = False

# if enabled, all ships except SPECIFIC_SHIP_NAME are skipped
CHECK_SPECIFIC_SHIP = False
SPECIFIC_SHIP_NAME = 'PLAYER_SHIP_CRACKED_MU_CIVILIAN_STATION_DAMAGED'
# if enabled, only ITERATION_LIMIT amount of ships will be processed
LIMIT_ITERATIONS = False
ITERATION_LIMIT = 1

parameters = [INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH, ADDON_OUTPUT_FOLDERPATH, SHIPS_TO_IGNORE, SAVE_ADDON, SAVE_ADDON,
              BACKUP_STANDALONE_SEGMENTS_FOR_DEVELOPER, BACKUP_STANDALONE_LAYOUTS_FOR_DEVELOPER, NR_GIBS,
              QUICK_AND_DIRTY_SEGMENT, CHECK_SPECIFIC_SHIP,
              SPECIFIC_SHIP_NAME, LIMIT_ITERATIONS, ITERATION_LIMIT]


def main(argv):
    globalStart = time.time()
    print("Starting Gib generation at %s, with parameters:" % globalStart)
    print(parameters)
    print("Loading ship file names...")
    ships = loadShipFileNames(INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH)
    nrShips = len(ships)
    nrShipsWithNewlyGeneratedGibs = 0
    nrShipsWithGibsAlreadyPresent = 0
    nrShipsWithIncompleteGibSetup = 0
    nrErrorsInMultiverseData = 0
    nrErrorsInSegmentation = 0
    nrErrorsInWeaponMounts = 0
    nrErrorsUnknownCause = 0
    nrIterations = 0
    totalLoadShipBaseImageDuration = 0
    totalSegmentDuration = 0
    totalSaveGibImagesDuration = 0
    totalAddGibEntriesToLayoutDuration = 0
    totalSetWeaponMountGibIdsDuration = 0
    totalSaveShipLayoutDuration = 0
    print("Iterating ships...")
    for name, filenames in ships.items():
        if CHECK_SPECIFIC_SHIP == True:
            if name != SPECIFIC_SHIP_NAME:
                continue
        if name in SHIPS_TO_IGNORE:
            print("Skipping %s" % name)
            continue
        nrIterations += 1
        printIterationInfo(globalStart, name, nrErrorsInMultiverseData, nrErrorsInSegmentation, nrErrorsInWeaponMounts,
                           nrErrorsUnknownCause, nrIterations, nrShips, nrShipsWithGibsAlreadyPresent,
                           nrShipsWithNewlyGeneratedGibs, nrShipsWithIncompleteGibSetup,
                           totalAddGibEntriesToLayoutDuration, totalSetWeaponMountGibIdsDuration,
                           totalLoadShipBaseImageDuration, totalSaveGibImagesDuration, totalSaveShipLayoutDuration,
                           totalSegmentDuration)
        shipImageName = filenames['img']
        layoutName = filenames['layout']

        # print('Processing %s ' % name)
        layout = loadShipLayout(layoutName, INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH)
        if layout == None:
            print('Cannot process layout for %s ' % name)
            nrErrorsInMultiverseData += 1
        elif areGibsPresentInLayout(layout) == True and areGibsPresentAsImageFiles(shipImageName,
                                                                                   INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH) == True:
            # print('Gibs already present for %s ' % name)
            nrShipsWithGibsAlreadyPresent += 1
        else:
            if areGibsPresentInLayout(layout) == True or areGibsPresentAsImageFiles(shipImageName,
                                                                                    INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH) == True:
                nrShipsWithIncompleteGibSetup += 1
                if areGibsPresentInLayout(layout) == True:
                    print("There are gibs in layout %s, but no images %s_gibN for it." % (layoutName, shipImageName))
                if areGibsPresentAsImageFiles(shipImageName, INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH) == True:
                    print("There are gib-images for base image %s, but no layout entries in %s for it." % (
                        shipImageName, layoutName))
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
                    appendContentString, totalSetWeaponMountGibIdsDuration, nrWeaponMountsWithoutGibId = setWeaponMountGibIdsWithProfiling(
                        gibs, layoutWithNewGibs, appendContentString, totalSetWeaponMountGibIdsDuration)
                    if nrWeaponMountsWithoutGibId > 0:
                        nrErrorsInWeaponMounts += 1
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
        "DONE. Created gibs for %u ships out of %u ships, %u of which had gibs before, %u of which had an incomplete gib setup. \nErrors when loading multiverse data: %u. Failed ship segmentations: %u. Ships with unassociated weaponMounts: %u. Unknown errors: %u" % (
            nrShipsWithNewlyGeneratedGibs, nrShips, nrShipsWithGibsAlreadyPresent, nrShipsWithIncompleteGibSetup,
            nrErrorsInMultiverseData, nrErrorsInSegmentation, nrErrorsInWeaponMounts, nrErrorsUnknownCause))
    print('Total runtime in minutes: %u' % ((time.time() - globalStart) / 60))


def saveShipLayoutWithProfiling(layoutName, layoutWithNewGibs, appendContentString, totalSaveShipLayoutDuration):
    start = time.time()
    if SAVE_STANDALONE == True:
        saveShipLayoutStandalone(layoutWithNewGibs, layoutName, INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH,
                                 developerBackup=BACKUP_STANDALONE_LAYOUTS_FOR_DEVELOPER)
    if SAVE_ADDON == True:
        saveShipLayoutAsAppendFile(appendContentString, layoutName, ADDON_OUTPUT_FOLDERPATH,
                                   developerBackup=False)
    totalSaveShipLayoutDuration += time.time() - start
    return totalSaveShipLayoutDuration


def addGibEntriesToLayoutWithProfiling(gibs, layout, totalAddGibEntriesToLayoutDuration):
    start = time.time()
    layoutWithNewGibs = addGibEntriesToLayout(layout, gibs)
    appendContentString = convertLayoutToAppendContent(layoutWithNewGibs)  # TODO: separate method
    totalAddGibEntriesToLayoutDuration += time.time() - start
    return layoutWithNewGibs, appendContentString, totalAddGibEntriesToLayoutDuration


def setWeaponMountGibIdsWithProfiling(gibs, layoutWithNewGibs, appendContentString, totalSetWeaponMountGibIdsDuration):
    start = time.time()
    additionalAppendContentString, nrWeaponMountsWithoutGibId = setWeaponMountGibIdsAsAppendContent(gibs,
                                                                                                    layoutWithNewGibs)
    appendContentString += additionalAppendContentString
    totalSetWeaponMountGibIdsDuration += time.time() - start
    return appendContentString, totalSetWeaponMountGibIdsDuration, nrWeaponMountsWithoutGibId


def saveGibImagesWithProfiling(gibs, shipImageName, shipImageSubfolder, totalSaveGibImagesDuration):
    start = time.time()
    if SAVE_STANDALONE == True:
        saveGibImages(gibs, shipImageName, shipImageSubfolder, INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH,
                      developerBackup=BACKUP_STANDALONE_SEGMENTS_FOR_DEVELOPER)
    if SAVE_ADDON == True:
        saveGibImages(gibs, shipImageName, shipImageSubfolder, ADDON_OUTPUT_FOLDERPATH,
                      developerBackup=False)
    totalSaveGibImagesDuration += time.time() - start
    return totalSaveGibImagesDuration


def segmentWithProfiling(baseImg, shipImageName, totalSegmentDuration):
    start = time.time()
    gibs = segment(baseImg, shipImageName, NR_GIBS, QUICK_AND_DIRTY_SEGMENT)
    totalSegmentDuration += time.time() - start
    return gibs, totalSegmentDuration


def loadShipBaseImageWithProfiling(shipImageName, totalLoadShipBaseImageDuration):
    start = time.time()
    baseImg, shipImageSubfolder = loadShipBaseImage(shipImageName, INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH)
    totalLoadShipBaseImageDuration += time.time() - start
    return baseImg, shipImageSubfolder, totalLoadShipBaseImageDuration


def printIterationInfo(globalStart, name, nrErrorsInMultiverseData, nrErrorsInSegmentation, nrErrorsInWeaponMounts,
                       nrErrorsUnknownCause, nrIterations, nrShips, nrShipsWithGibsAlreadyPresent,
                       nrShipsWithNewlyGeneratedGibs, nrShipsWithIncompleteGibSetup, totalAddGibEntriesToLayoutDuration,
                       totalSetWeaponMountGibIdsDuration, totalLoadShipBaseImageDuration, totalSaveGibImagesDuration,
                       totalSaveShipLayoutDuration, totalSegmentDuration):
    if (nrIterations % 1) == 0:
        elapsedMinutes = (time.time() - globalStart) / 60.
        finishedFraction = (nrIterations / float(nrShips))
        remainingFraction = 1. - finishedFraction
        remainingMinutes = elapsedMinutes * remainingFraction / finishedFraction
        print(
            "Iterating ships: %u / %u (%.0f%%), elapsed %u minutes, remaining %u minutes, current entry: %s; new: %u, untouched: %u, incomplete in MV: %u, errors MV: %u, errors SLIC: %u, errors weaponMounts: %u, unknown errors: %u" % (
                nrIterations, nrShips, 100. * finishedFraction, elapsedMinutes, remainingMinutes, name,
                nrShipsWithNewlyGeneratedGibs, nrShipsWithGibsAlreadyPresent, nrShipsWithIncompleteGibSetup,
                nrErrorsInMultiverseData, nrErrorsInSegmentation, nrErrorsInWeaponMounts, nrErrorsUnknownCause))
    if (nrIterations % 5) == 0:  # note that this is BEFORE the current iteration has finished!
        totalDuration = totalLoadShipBaseImageDuration + totalSegmentDuration + totalSaveGibImagesDuration + totalAddGibEntriesToLayoutDuration + totalSetWeaponMountGibIdsDuration + totalSaveShipLayoutDuration
        if totalDuration > 0:
            totalLoadShipBaseImagePercentage = round(100. * totalLoadShipBaseImageDuration / totalDuration)
            totalSegmentDurationPercentage = round(100. * totalSegmentDuration / totalDuration)
            totalSaveGibImagesDurationPercentage = round(100. * totalSaveGibImagesDuration / totalDuration)
            totalAddGibEntriesToLayoutDurationPercentage = round(
                100. * totalAddGibEntriesToLayoutDuration / totalDuration)
            totalSetWeaponMountGibIdsDurationPercentage = round(
                100. * totalSetWeaponMountGibIdsDuration / totalDuration)
            totalSaveShipLayoutDurationPercentage = round(100. * totalSaveShipLayoutDuration / totalDuration)
            print(
                "PROFILING: average profiled duration per iteration: %.3f seconds, loadShipBaseImage: %u%%, segment: %u%%, saveGibImages: %u%%, addGibEntriesToLayout: %u%%, totalSetWeaponMountGibIdsDurationPercentage: %u%%, saveShipLayout: %u%%" % (
                    (totalDuration / (nrIterations - 1.)), totalLoadShipBaseImagePercentage,
                    totalSegmentDurationPercentage, totalSaveGibImagesDurationPercentage,
                    totalAddGibEntriesToLayoutDurationPercentage, totalSetWeaponMountGibIdsDurationPercentage,
                    totalSaveShipLayoutDurationPercentage))


if __name__ == '__main__':
    main(sys.argv)
