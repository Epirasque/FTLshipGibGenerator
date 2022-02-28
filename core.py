import sys
import time

from fileHandling.gibImageChecker import areGibsPresentAsImageFiles
from fileHandling.gibImageSaver import saveGibImages
from fileHandling.shipBlueprintLoader import loadShipFileNames
from fileHandling.shipImageLoader import loadShipBaseImage
from fileHandling.shipLayoutDao import loadShipLayout, saveShipLayoutStandalone, saveShipLayoutAsAppendFile
from flow.sameLayoutGibMaskReuser import generateGibsBasedOnSameLayoutGibMask
from imageProcessing.segmenter import segment
from metadata.gibEntryAdder import addGibEntriesToLayout
from metadata.gibEntryChecker import areGibsPresentInLayout
from metadata.layoutToAppendContentConverter import convertLayoutToAppendContent
from metadata.weaponMountGibIdUpdater import setWeaponMountGibIdsAsAppendContent

# Source for metadata semantics: https://www.ftlwiki.com/wiki/Modding_ships

# note: use / instead of \ to avoid character-escaping issues
INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH = 'FTL-Multiverse 5.1 Hotfix'  # 'FTL-Multiverse 5.1 Hotfix'
ADDON_OUTPUT_FOLDERPATH = 'MV Addon GenGibs v0.9.1'  # e.g. 'MV Addon GenGibs v0.9'
# tutorial is part of vanilla and should have gibs. MU_COALITION_CONSTRUCTION seems to be a bug in MV, has no layout file
SHIPS_TO_IGNORE = ['PLAYER_SHIP_TUTORIAL', 'MU_COALITION_CONSTRUCTION']
# configure whether the output is meant for standalone or as an addon.
# KEEP A BACKUP READY! it is best practice to restore the backup before generating new gibs, .bat files can help a lot for that
SAVE_STANDALONE = True
SAVE_ADDON = True
# if enabled, save a separate copy of the output in gibs and/or layouts folders;
# these have to exist as subfolders of glaive and they are NOT cleaned up automatically
BACKUP_STANDALONE_SEGMENTS_FOR_DEVELOPER = False
BACKUP_STANDALONE_LAYOUTS_FOR_DEVELOPER = False

# actual number can be less: if the algorithm has an issue it is retried with fewer gibs
NR_GIBS = 5
# enable for sanity checks
QUICK_AND_DIRTY_SEGMENT = False

# if enabled, all ships except SPECIFIC_SHIP_NAME are skipped
CHECK_SPECIFIC_SHIPS = False
SPECIFIC_SHIP_NAMES = ['MU_FED_SCOUT', 'MU_FED_SCOUT_ELITE']
# if enabled, only ITERATION_LIMIT amount of ships will be processed
LIMIT_ITERATIONS = False
ITERATION_LIMIT = 1

parameters = [INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH, ADDON_OUTPUT_FOLDERPATH, SHIPS_TO_IGNORE, SAVE_ADDON, SAVE_ADDON,
              BACKUP_STANDALONE_SEGMENTS_FOR_DEVELOPER, BACKUP_STANDALONE_LAYOUTS_FOR_DEVELOPER, NR_GIBS,
              QUICK_AND_DIRTY_SEGMENT, CHECK_SPECIFIC_SHIPS,
              SPECIFIC_SHIP_NAMES, LIMIT_ITERATIONS, ITERATION_LIMIT]


def main(argv):
    globalStart = time.time()
    print("Starting Gib generation at %s, with parameters:" % globalStart)
    print(parameters)
    print("Loading ship file names...")
    ships = loadShipFileNames(INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH)
    stats = {'nrShips': len(ships),
             'nrShipsWithNewlyGeneratedGibs': 0,
             'nrShipsWithGibsAlreadyPresent': 0,
             'nrShipsWithIncompleteGibSetup': 0,
             'nrErrorsInsource': 0,
             'nrErrorsInSegmentation': 0,
             'nrErrorsInWeaponMounts': 0,
             'nrErrorsUnknownCause': 0,
             'nrIterations': 0,
             'totalLoadShipBaseImageDuration': 0,
             'totalSegmentDuration': 0,
             'totalSaveGibImagesDuration': 0,
             'totalAddGibEntriesToLayoutDuration': 0,
             'totalSetWeaponMountGibIdsDuration': 0,
             'totalSaveShipLayoutDuration': 0}
    print("Iterating ships...")
    layoutNameToGibsAndSubfolder = {}
    for name, filenames in ships.items():
        if CHECK_SPECIFIC_SHIPS == True:
            if name not in SPECIFIC_SHIP_NAMES:
                continue
        if name in SHIPS_TO_IGNORE:
            print("Skipping %s" % name)
            continue
        stats['nrIterations'] += 1
        printIterationInfo(globalStart, name, stats)
        shipImageName = filenames['img']
        layoutName = filenames['layout']

        # print('Processing %s ' % name)
        layout = loadShipLayout(layoutName, INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH)
        if layout == None:
            print('Cannot process layout for %s ' % name)
            stats['nrErrorsInsource'] += 1
        elif hasShipGibs(layout, shipImageName):
            # print('Gibs already present for %s ' % name)
            stats['nrShipsWithGibsAlreadyPresent'] += 1
        else:
            stats, layoutNameToGibsAndSubfolder = createNewGibs(layout, layoutName, layoutNameToGibsAndSubfolder, name,
                                                                shipImageName, ships, stats)

        if LIMIT_ITERATIONS == True and stats['nrIterations'] >= ITERATION_LIMIT:
            break

    print(
        "DONE. Created gibs for %u ships out of %u ships, %u of which had gibs before, %u of which had an incomplete gib setup. \nErrors when loading source: %u. Failed ship segmentations: %u. Ships with unassociated weaponMounts: %u. Unknown errors: %u" % (
            stats['nrShipsWithNewlyGeneratedGibs'], stats['nrShips'], stats['nrShipsWithGibsAlreadyPresent'],
            stats['nrShipsWithIncompleteGibSetup'], stats['nrErrorsInsource'], stats['nrErrorsInSegmentation'],
            stats['nrErrorsInWeaponMounts'], stats['nrErrorsUnknownCause']))
    print('Total runtime in minutes: %u' % ((time.time() - globalStart) / 60))


def createNewGibs(layout, layoutName, layoutNameToGibsAndSubfolder, name, shipImageName, ships, stats):
    foundGibsSameLayout = False
    gibs = []
    shipImageSubfolder = 'not set'
    if areGibsPresentInLayout(layout) == True:
        foundGibsSameLayout, gibs, shipImageSubfolder = attemptGeneratingGibsFromIdenticalLayout(layout,
                                                                                                 layoutName,
                                                                                                 layoutNameToGibsAndSubfolder,
                                                                                                 name, shipImageName,
                                                                                                 ships, stats)
    if foundGibsSameLayout == True:
        print("Succeeded in generating gibs with mask of gibs from same layout")
        stats = saveGibImagesWithProfiling(gibs, shipImageName, shipImageSubfolder, stats)
        layoutNameToGibsAndSubfolder[layoutName] = gibs, shipImageSubfolder
    else:
        if areGibsPresentAsImageFiles(shipImageName, INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH) == True:
            stats['nrShipsWithIncompleteGibSetup'] += 1
            print("There are gib-images for base image %s, but no layout entries in %s for it." % (
                shipImageName, layoutName))
        try:
            stats, gibs, shipImageSubfolder = generateGibsForShip(layout, layoutName, shipImageName, stats)
            layoutNameToGibsAndSubfolder[layoutName] = gibs, shipImageSubfolder
        except Exception as e:
            print("UNEXPECTED EXCEPTION: %s" % e)
            stats['nrErrorsUnknownCause'] += 1
    return stats, layoutNameToGibsAndSubfolder


def attemptGeneratingGibsFromIdenticalLayout(layout, layoutName,
                                             layoutNameToGibsAndSubfolder, name, shipImageName,
                                             ships, stats):
    stats['nrShipsWithIncompleteGibSetup'] += 1  # TODO: separate profiling / stat case
    print("There are gibs in layout %s, but no images %s_gibN for it." % (layoutName, shipImageName))
    gibs = []
    shipImageSubfolder = 'not set'
    foundGibsSameLayout = False
    try:
        print('Trying to find gibs already existing for the layout before this run...')
        foundGibsSameLayout, gibs, shipImageSubfolder = generateGibsBasedOnSameLayoutGibMask(layout,
                                                                                             layoutName,
                                                                                             name, NR_GIBS,
                                                                                             shipImageName,
                                                                                             ships,
                                                                                             INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH,
                                                                                             layoutNameToGibsAndSubfolder)
    except Exception as e:
        print("UNEXPECTED EXCEPTION: %s" % e)
        stats['nrErrorsUnknownCause'] += 1
    return foundGibsSameLayout, gibs, shipImageSubfolder


def generateGibsForShip(layout, layoutName, shipImageName, stats):
    baseImg, shipImageSubfolder, stats = loadShipBaseImageWithProfiling(shipImageName, stats)
    gibs, stats = segmentWithProfiling(baseImg, shipImageName, stats)
    if len(gibs) == 0:
        stats['nrErrorsInSegmentation'] += 1
    else:
        stats = saveGibImagesWithProfiling(gibs, shipImageName, shipImageSubfolder, stats)
        layoutWithNewGibs, appendContentString, stats = addGibEntriesToLayoutWithProfiling(gibs, layout, stats)
        appendContentString, nrWeaponMountsWithoutGibId, stats = setWeaponMountGibIdsWithProfiling(gibs,
                                                                                                   layoutWithNewGibs,
                                                                                                   appendContentString,
                                                                                                   stats)
        if nrWeaponMountsWithoutGibId > 0:
            stats['nrErrorsInWeaponMounts'] += 1
        stats = saveShipLayoutWithProfiling(layoutName, layoutWithNewGibs, appendContentString, stats)
        # print("Done with %s " % name)
        stats['nrShipsWithNewlyGeneratedGibs'] += 1
    return stats, gibs, shipImageSubfolder


def hasShipGibs(layout, shipImageName):
    return areGibsPresentInLayout(layout) == True and areGibsPresentAsImageFiles(shipImageName,
                                                                                 INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH) == True


def saveShipLayoutWithProfiling(layoutName, layoutWithNewGibs, appendContentString, stats):
    start = time.time()
    if SAVE_STANDALONE == True:
        saveShipLayoutStandalone(layoutWithNewGibs, layoutName, INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH,
                                 developerBackup=BACKUP_STANDALONE_LAYOUTS_FOR_DEVELOPER)
    if SAVE_ADDON == True:
        saveShipLayoutAsAppendFile(appendContentString, layoutName, ADDON_OUTPUT_FOLDERPATH, developerBackup=False)
    stats['totalSaveShipLayoutDuration'] += time.time() - start
    return stats


def addGibEntriesToLayoutWithProfiling(gibs, layout, stats):
    start = time.time()
    layoutWithNewGibs = addGibEntriesToLayout(layout, gibs)
    appendContentString = convertLayoutToAppendContent(layoutWithNewGibs)  # TODO: separate method
    stats['totalAddGibEntriesToLayoutDuration'] += time.time() - start
    return layoutWithNewGibs, appendContentString, stats


def setWeaponMountGibIdsWithProfiling(gibs, layoutWithNewGibs, appendContentString, stats):
    start = time.time()
    additionalAppendContentString, nrWeaponMountsWithoutGibId = setWeaponMountGibIdsAsAppendContent(gibs,
                                                                                                    layoutWithNewGibs)
    appendContentString += additionalAppendContentString
    stats['totalSetWeaponMountGibIdsDuration'] += time.time() - start
    return appendContentString, nrWeaponMountsWithoutGibId, stats


def saveGibImagesWithProfiling(gibs, shipImageName, shipImageSubfolder, stats):
    start = time.time()
    if SAVE_STANDALONE == True:
        saveGibImages(gibs, shipImageName, shipImageSubfolder, INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH,
                      developerBackup=BACKUP_STANDALONE_SEGMENTS_FOR_DEVELOPER)
    if SAVE_ADDON == True:
        saveGibImages(gibs, shipImageName, shipImageSubfolder, ADDON_OUTPUT_FOLDERPATH, developerBackup=False)
    stats['totalSaveGibImagesDuration'] += time.time() - start
    return stats


def segmentWithProfiling(baseImg, shipImageName, stats):
    start = time.time()
    gibs = segment(baseImg, shipImageName, NR_GIBS, QUICK_AND_DIRTY_SEGMENT)
    stats['totalSegmentDuration'] += time.time() - start
    return gibs, stats


def loadShipBaseImageWithProfiling(shipImageName, stats):
    start = time.time()
    baseImg, shipImageSubfolder = loadShipBaseImage(shipImageName, INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH)
    stats['totalLoadShipBaseImageDuration'] += time.time() - start
    return baseImg, shipImageSubfolder, stats


def printIterationInfo(globalStart, name, stats):
    if (stats['nrIterations'] % 1) == 0:
        elapsedMinutes = (time.time() - globalStart) / 60.
        finishedFraction = (stats['nrIterations'] / float(stats['nrShips']))
        remainingFraction = 1. - finishedFraction
        remainingMinutes = elapsedMinutes * remainingFraction / finishedFraction
        print(
            "Iterating ships: %u / %u (%.0f%%), elapsed %u minutes, remaining %u minutes, current entry: %s; new: %u, untouched: %u, incomplete in source: %u, errors in source: %u, errors SLIC: %u, errors weaponMounts: %u, unknown errors: %u" % (
                stats['nrIterations'], stats['nrShips'], 100. * finishedFraction, elapsedMinutes, remainingMinutes,
                name,
                stats['nrShipsWithNewlyGeneratedGibs'], stats['nrShipsWithGibsAlreadyPresent'],
                stats['nrShipsWithIncompleteGibSetup'],
                stats['nrErrorsInsource'], stats['nrErrorsInSegmentation'], stats['nrErrorsInWeaponMounts'],
                stats['nrErrorsUnknownCause']))
    if (stats['nrIterations'] % 5) == 0:  # note that this is BEFORE the current iteration has finished!
        totalDuration = stats['totalLoadShipBaseImageDuration'] + stats['totalSegmentDuration'] + stats[
            'totalSaveGibImagesDuration'] + stats['totalAddGibEntriesToLayoutDuration'] + stats[
                            'totalSetWeaponMountGibIdsDuration'] + stats['totalSaveShipLayoutDuration']
        if totalDuration > 0:
            totalLoadShipBaseImagePercentage = round(100. * stats['totalLoadShipBaseImageDuration'] / totalDuration)
            totalSegmentDurationPercentage = round(100. * stats['totalSegmentDuration'] / totalDuration)
            totalSaveGibImagesDurationPercentage = round(100. * stats['totalSaveGibImagesDuration'] / totalDuration)
            totalAddGibEntriesToLayoutDurationPercentage = round(
                100. * stats['totalAddGibEntriesToLayoutDuration'] / totalDuration)
            totalSetWeaponMountGibIdsDurationPercentage = round(
                100. * stats['totalSetWeaponMountGibIdsDuration'] / totalDuration)
            totalSaveShipLayoutDurationPercentage = round(100. * stats['totalSaveShipLayoutDuration'] / totalDuration)
            print(
                "PROFILING: average profiled duration per iteration: %.3f seconds, loadShipBaseImage: %u%%, segment: %u%%, saveGibImages: %u%%, addGibEntriesToLayout: %u%%, totalSetWeaponMountGibIdsDurationPercentage: %u%%, saveShipLayout: %u%%" % (
                    (totalDuration / (stats['nrIterations'] - 1.)), totalLoadShipBaseImagePercentage,
                    totalSegmentDurationPercentage, totalSaveGibImagesDurationPercentage,
                    totalAddGibEntriesToLayoutDurationPercentage, totalSetWeaponMountGibIdsDurationPercentage,
                    totalSaveShipLayoutDurationPercentage))


if __name__ == '__main__':
    main(sys.argv)
