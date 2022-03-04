import shutil
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


def startGeneratorLoop(parameters):
    globalStart = time.time()
    print("Starting Gib generation at %s, with parameters:" % globalStart)
    print(parameters)
    print("Loading ship file names...")
    ships = loadShipFileNames(parameters.INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH)
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
    print("Cleaning up gibCache...")
    try:
        shutil.rmtree('gibCache')
    except OSError as e:
        print("Did not clean gibCache (e.g. folder was already cleaned up): %s" % e)
    except Exception as e:
        print("EXCEPTION when cleaning up gibCache: %s" % e)
    print("Iterating ships...")
    layoutNameToGibCache = {}
    for name, filenames in ships.items():
        if parameters.CHECK_SPECIFIC_SHIPS == True:
            if name not in parameters.SPECIFIC_SHIP_NAMES:
                continue
        if name in parameters.SHIPS_TO_IGNORE:
            print("Skipping %s" % name)
            continue
        stats['nrIterations'] += 1
        printIterationInfo(globalStart, name, stats)
        shipImageName = filenames['img']
        layoutName = filenames['layout']

        # print('Processing %s ' % name)
        layout = loadShipLayout(layoutName, parameters.INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH)
        if layout == None:
            print('Cannot process layout for %s ' % name)
            stats['nrErrorsInsource'] += 1
        elif hasShipGibs(parameters, layout, shipImageName):
            # print('Gibs already present for %s ' % name)
            stats['nrShipsWithGibsAlreadyPresent'] += 1
        else:
            stats, layoutNameToGibCache = createNewGibs(parameters, layout, layoutName,
                                                                layoutNameToGibCache, name,
                                                                shipImageName, ships, stats)

        if parameters.LIMIT_ITERATIONS == True and stats['nrIterations'] >= parameters.ITERATION_LIMIT:
            break

    print(
        "DONE. Created gibs for %u ships out of %u ships, %u of which had gibs before, %u of which had an incomplete gib setup. \nErrors when loading source: %u. Failed ship segmentations: %u. Ships with unassociated weaponMounts: %u. Unknown errors: %u" % (
            stats['nrShipsWithNewlyGeneratedGibs'], stats['nrShips'], stats['nrShipsWithGibsAlreadyPresent'],
            stats['nrShipsWithIncompleteGibSetup'], stats['nrErrorsInsource'], stats['nrErrorsInSegmentation'],
            stats['nrErrorsInWeaponMounts'], stats['nrErrorsUnknownCause']))
    print("Cleaning up gibCache...")
    try:
        shutil.rmtree('gibCache')
    except OSError as e:
        print("Did not clean gibCache (e.g. folder was already cleaned up): %s" % e)
    except Exception as e:
        print("UNEXPECTED EXCEPTION when cleaning up gibCache: %s" % e)
    print('Total runtime in minutes: %u' % ((time.time() - globalStart) / 60))


def createNewGibs(parameters, layout, layoutName, layoutNameToGibCache, name, shipImageName, ships, stats):
    foundGibsSameLayout = False
    gibs = []
    shipImageSubfolder = 'not set'
    if areGibsPresentInLayout(layout) == True:
        foundGibsSameLayout, gibs, shipImageSubfolder = attemptGeneratingGibsFromIdenticalLayout(parameters, layout,
                                                                                                 layoutName,
                                                                                                 layoutNameToGibCache,
                                                                                                 name, shipImageName,
                                                                                                 ships, stats)
    if foundGibsSameLayout == True:
        print("Succeeded in generating gibs with mask of gibs from same layout")
        stats = saveGibImagesWithProfiling(parameters, gibs, shipImageName, shipImageSubfolder, stats)
    else:
        if areGibsPresentAsImageFiles(shipImageName, parameters.INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH) == True:
            stats['nrShipsWithIncompleteGibSetup'] += 1
            print("There are gib-images for base image %s, but no layout entries in %s for it." % (
                shipImageName, layoutName))
        try:
            stats, gibs, shipImageSubfolder, layoutWithNewGibs = generateGibsForShip(parameters, layout, layoutName, shipImageName, stats)
            layoutNameToGibCache[layoutName] = shipImageName, len(gibs), layoutWithNewGibs
        except Exception as e:
            print("UNEXPECTED EXCEPTION: %s" % e)
            stats['nrErrorsUnknownCause'] += 1
    return stats, layoutNameToGibCache


def attemptGeneratingGibsFromIdenticalLayout(parameters, layout, layoutName,
                                             layoutNameToGibCache, name, shipImageName,
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
                                                                                             name, parameters.NR_GIBS,
                                                                                             shipImageName,
                                                                                             ships,
                                                                                             parameters.INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH,
                                                                                             layoutNameToGibCache)
    except Exception as e:
        print("UNEXPECTED EXCEPTION: %s" % e)
        stats['nrErrorsUnknownCause'] += 1
    return foundGibsSameLayout, gibs, shipImageSubfolder


def generateGibsForShip(parameters, layout, layoutName, shipImageName, stats):
    baseImg, shipImageSubfolder, stats = loadShipBaseImageWithProfiling(parameters, shipImageName, stats)
    gibs, stats = segmentWithProfiling(parameters, baseImg, shipImageName, stats)
    if len(gibs) == 0:
        stats['nrErrorsInSegmentation'] += 1
    else:
        stats = saveGibImagesWithProfiling(parameters, gibs, shipImageName, shipImageSubfolder, stats)
        layoutWithNewGibs, appendContentString, stats = addGibEntriesToLayoutWithProfiling(gibs, layout, stats)
        appendContentString, nrWeaponMountsWithoutGibId, stats = setWeaponMountGibIdsWithProfiling(gibs,
                                                                                                   layoutWithNewGibs,
                                                                                                   appendContentString,
                                                                                                   stats)
        if nrWeaponMountsWithoutGibId > 0:
            stats['nrErrorsInWeaponMounts'] += 1
        stats = saveShipLayoutWithProfiling(parameters, layoutName, layoutWithNewGibs, appendContentString, stats)
        # print("Done with %s " % name)
        stats['nrShipsWithNewlyGeneratedGibs'] += 1
    return stats, gibs, shipImageSubfolder, layoutWithNewGibs


def hasShipGibs(parameters, layout, shipImageName):
    return areGibsPresentInLayout(layout) == True and areGibsPresentAsImageFiles(shipImageName,
                                                                                 parameters.INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH) == True


def saveShipLayoutWithProfiling(parameters, layoutName, layoutWithNewGibs, appendContentString, stats):
    start = time.time()
    if parameters.SAVE_STANDALONE == True:
        saveShipLayoutStandalone(layoutWithNewGibs, layoutName, parameters.INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH,
                                 developerBackup=parameters.BACKUP_STANDALONE_LAYOUTS_FOR_DEVELOPER)
    if parameters.SAVE_ADDON == True:
        saveShipLayoutAsAppendFile(appendContentString, layoutName, parameters.ADDON_OUTPUT_FOLDERPATH,
                                   developerBackup=False)
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


def saveGibImagesWithProfiling(parameters, gibs, shipImageName, shipImageSubfolder, stats):
    start = time.time()
    if parameters.SAVE_STANDALONE == True:
        saveGibImages(gibs, shipImageName, shipImageSubfolder, parameters.INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH,
                      developerBackup=parameters.BACKUP_STANDALONE_SEGMENTS_FOR_DEVELOPER)
    if parameters.SAVE_ADDON == True:
        saveGibImages(gibs, shipImageName, shipImageSubfolder, parameters.ADDON_OUTPUT_FOLDERPATH,
                      developerBackup=False)
    stats['totalSaveGibImagesDuration'] += time.time() - start
    return stats


def segmentWithProfiling(parameters, baseImg, shipImageName, stats):
    start = time.time()
    gibs = segment(baseImg, shipImageName, parameters.NR_GIBS, parameters.QUICK_AND_DIRTY_SEGMENT)
    stats['totalSegmentDuration'] += time.time() - start
    return gibs, stats


def loadShipBaseImageWithProfiling(parameters, shipImageName, stats):
    start = time.time()
    baseImg, shipImageSubfolder = loadShipBaseImage(shipImageName, parameters.INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH)
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
