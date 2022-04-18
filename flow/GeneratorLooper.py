import datetime
import logging
import shutil
import time
import traceback
import tracemalloc
from copy import deepcopy

from fileHandling.GibImageChecker import areGibsPresentAsImageFiles
from fileHandling.GibImageSaver import saveGibImages, saveGibImagesToDiskCache
from fileHandling.MetalBitsLoader import loadTilesets
from fileHandling.ShipBlueprintLoader import loadShipFileNames
from fileHandling.ShipImageLoader import loadShipBaseImage
from fileHandling.ShipLayoutDao import loadShipLayout, saveShipLayoutStandalone, saveShipLayoutAsAppendFile
from flow.MemoryManagement import logHighestMemoryUsage, cleanUpMemory
from flow.SameLayoutGibMaskReuser import generateGibsBasedOnSameLayoutGibMask
from imageProcessing.MetalBitsAttacher import attachMetalBits
from imageProcessing.Segmenter import segment
from metadata.GibEntryAdder import addGibEntriesToLayout
from metadata.GibEntryChecker import areGibsPresentInLayout
from metadata.LayoutToAppendContentConverter import convertLayoutToAppendContent
from metadata.WeaponMountGibIdUpdater import setWeaponMountGibIdsAsAppendContent

logger = logging.getLogger('GLAIVE.' + __name__)

STANDALONE_MODE = 'standalone'
ADDON_MODE = 'addon'


def startGeneratorLoop(PARAMETERS):
    globalStart = time.time()
    logger.info(
        "Starting Gib generation at %s, with PARAMETERS:" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    logger.info(PARAMETERS)
    tracemalloc.start()
    logger.info("Loading ship file names...")
    ships = loadShipFileNames(PARAMETERS.INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH)
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
    logger.info("Cleaning up gibCache...")
    try:
        shutil.rmtree('gibCache')
    except OSError as e:
        logger.info("Did not clean gibCache (e.g. folder was already cleaned up): %s" % e)
    except Exception as e:
        logger.warning("EXCEPTION when cleaning up gibCache: %s" % e)
    tilesets = {}
    if (PARAMETERS.GENERATE_METAL_BITS == True):
        tilesets = loadTilesets()
    logger.info("Iterating ships...")
    layoutNameToGibCache = {}
    for shipName, filenames in ships.items():
        cleanUpMemory()
        if PARAMETERS.CHECK_SPECIFIC_SHIPS == True:
            if shipName not in PARAMETERS.SPECIFIC_SHIP_NAMES:
                continue
        if shipName in PARAMETERS.SHIPS_TO_IGNORE:
            logger.info("Skipping %s" % shipName)
            continue
        stats['nrIterations'] += 1
        layoutName = filenames['layout']
        shipImageName = filenames['img']
        printIterationInfo(globalStart, shipName, layoutName, shipImageName, stats)

        # print('Processing %s ' % name)
        layout = loadShipLayout(layoutName, PARAMETERS.INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH)
        if layout == None:
            logger.error('Cannot process layout for %s ' % shipName)
            stats['nrErrorsInsource'] += 1
        elif hasShipGibs(PARAMETERS, layout, shipImageName):
            # print('Gibs already present for %s ' % name)
            stats['nrShipsWithGibsAlreadyPresent'] += 1
        else:
            stats, layoutNameToGibCache = createNewGibs(PARAMETERS, layout, layoutName,
                                                        layoutNameToGibCache, shipName,
                                                        shipImageName, ships, stats, tilesets)

        if PARAMETERS.LIMIT_ITERATIONS == True and stats['nrIterations'] >= PARAMETERS.ITERATION_LIMIT:
            break

    logger.info(
        "DONE. Created gibs for %u ships out of %u ships, %u of which had gibs before, %u of which had an incomplete gib setup. \nErrors when loading source: %u. Failed ship segmentations: %u. Ships with unassociated weaponMounts: %u. Unknown errors: %u" % (
            stats['nrShipsWithNewlyGeneratedGibs'], stats['nrShips'], stats['nrShipsWithGibsAlreadyPresent'],
            stats['nrShipsWithIncompleteGibSetup'], stats['nrErrorsInsource'], stats['nrErrorsInSegmentation'],
            stats['nrErrorsInWeaponMounts'], stats['nrErrorsUnknownCause']))
    logger.info("Cleaning up gibCache...")
    try:
        shutil.rmtree('gibCache')
    except OSError as e:
        logger.info("Did not clean gibCache (e.g. folder was already cleaned up): %s" % e)
    except Exception:
        logger.warning("UNEXPECTED EXCEPTION when cleaning up gibCache: %s" % traceback.format_exc())
    logger.info('Total runtime in minutes: %u' % ((time.time() - globalStart) / 60))


def createNewGibs(PARAMETERS, layout, layoutName, layoutNameToGibCache, name, shipImageName, ships, stats, tilesets):
    foundGibsSameLayout = False
    gibs = []
    folderPath = 'not set'
    if layoutName in layoutNameToGibCache:
        logger.debug('Found layout already filled in this run')
        shipImageNameInCache, nrGibs, layout = layoutNameToGibCache[layoutName]
    if areGibsPresentInLayout(layout) == True:
        foundGibsSameLayout, gibs, newGibsWithoutMetalBits, folderPath = attemptGeneratingGibsFromIdenticalLayout(
            PARAMETERS, tilesets, layout,
            layoutName,
            layoutNameToGibCache,
            name, shipImageName,
            ships, stats)
    if foundGibsSameLayout == True:
        logger.debug("Succeeded in generating gibs with mask of gibs from same layout")
        stats = saveGibImagesWithProfiling(PARAMETERS, gibs, newGibsWithoutMetalBits, shipImageName, folderPath, stats)
    else:
        if areGibsPresentAsImageFiles(shipImageName, PARAMETERS.INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH) == True:
            stats['nrShipsWithIncompleteGibSetup'] += 1
            logger.debug("There are gib-images for base image %s, but no layout entries in %s for it." % (
                shipImageName, layoutName))
        try:
            stats, gibs, shipImageSubfolder, layoutWithNewGibs = generateGibsForShip(PARAMETERS, layout, layoutName,
                                                                                     shipImageName, stats, tilesets)
            layoutNameToGibCache[layoutName] = shipImageName, len(gibs), layoutWithNewGibs
        except Exception:
            logger.error("UNEXPECTED EXCEPTION: %s" % traceback.format_exc())
            stats['nrErrorsUnknownCause'] += 1
    return stats, layoutNameToGibCache


def attemptGeneratingGibsFromIdenticalLayout(PARAMETERS, tilesets, layout, layoutName,
                                             layoutNameToGibCache, name, shipImageName,
                                             ships, stats):
    stats['nrShipsWithIncompleteGibSetup'] += 1  # TODO: separate profiling / stat case
    logger.debug("There are gibs in layout %s, but no images %s_gibN for it." % (layoutName, shipImageName))
    newGibsWithMetalBits = []
    newGibsWithoutMetalBits = []
    folderPath = 'not set'
    foundGibsSameLayout = False
    try:
        logger.debug('Trying to find gibs already existing for the layout before this run...')
        targetFolderPath = determineTargetFolderPath(PARAMETERS)
        foundGibsSameLayout, newGibsWithMetalBits, newGibsWithoutMetalBits, folderPath = generateGibsBasedOnSameLayoutGibMask(
            PARAMETERS, tilesets, layout,
            layoutName,
            name, PARAMETERS.NR_GIBS,
            shipImageName,
            ships,
            PARAMETERS.INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH,
            targetFolderPath,
            layoutNameToGibCache)
    except Exception:
        logger.error("UNEXPECTED EXCEPTION: %s" % traceback.format_exc())
        stats['nrErrorsUnknownCause'] += 1
    return foundGibsSameLayout, newGibsWithMetalBits, newGibsWithoutMetalBits, folderPath


def determineTargetFolderPath(PARAMETERS):
    targetFolderPath = 'unset'
    if PARAMETERS.OUTPUT_MODE == STANDALONE_MODE:
        targetFolderPath = PARAMETERS.INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH
    if PARAMETERS.OUTPUT_MODE == ADDON_MODE:
        targetFolderPath = PARAMETERS.ADDON_OUTPUT_FOLDERPATH
    return targetFolderPath


def generateGibsForShip(PARAMETERS, layout, layoutName, shipImageName, stats, tilesets):
    baseImg, shipImageSubfolder, stats = loadShipBaseImageWithProfiling(PARAMETERS, shipImageName, stats)
    gibs, stats = segmentWithProfiling(PARAMETERS, baseImg, shipImageName, stats)
    gibsWithoutMetalBits = deepcopy(gibs)
    if PARAMETERS.GENERATE_METAL_BITS == True:
        gibs = attachMetalBits(gibs, baseImg, tilesets, PARAMETERS, shipImageName)
    if len(gibs) == 0:
        stats['nrErrorsInSegmentation'] += 1
    else:
        targetFolderPath = determineTargetFolderPath(PARAMETERS)
        targetFolderPath += '\\img\\' + shipImageSubfolder
        stats = saveGibImagesWithProfiling(PARAMETERS, gibs, gibsWithoutMetalBits, shipImageName, targetFolderPath,
                                           stats)
        layoutWithNewGibs, appendContentString, stats = addGibEntriesToLayoutWithProfiling(gibs, layout, stats)
        appendContentString, nrWeaponMountsWithoutGibId, stats = setWeaponMountGibIdsWithProfiling(gibs,
                                                                                                   layoutWithNewGibs,
                                                                                                   appendContentString,
                                                                                                   stats)
        if nrWeaponMountsWithoutGibId > 0:
            stats['nrErrorsInWeaponMounts'] += 1
        stats = saveShipLayoutWithProfiling(PARAMETERS, layoutName, layoutWithNewGibs, appendContentString, stats)
        # print("Done with %s " % name)
        stats['nrShipsWithNewlyGeneratedGibs'] += 1
    return stats, gibs, shipImageSubfolder, layoutWithNewGibs


def hasShipGibs(PARAMETERS, layout, shipImageName):
    return areGibsPresentInLayout(layout) == True and areGibsPresentAsImageFiles(shipImageName,
                                                                                 PARAMETERS.INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH) == True


def saveShipLayoutWithProfiling(PARAMETERS, layoutName, layoutWithNewGibs, appendContentString, stats):
    start = time.time()
    if PARAMETERS.OUTPUT_MODE == STANDALONE_MODE:
        saveShipLayoutStandalone(layoutWithNewGibs, layoutName, PARAMETERS.INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH,
                                 developerBackup=PARAMETERS.BACKUP_LAYOUTS_FOR_DEVELOPER)
    if PARAMETERS.OUTPUT_MODE == ADDON_MODE:
        saveShipLayoutAsAppendFile(appendContentString, layoutName, PARAMETERS.ADDON_OUTPUT_FOLDERPATH,
                                   developerBackup=PARAMETERS.BACKUP_LAYOUTS_FOR_DEVELOPER)
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


def saveGibImagesWithProfiling(PARAMETERS, gibs, gibsWithoutMetalBits, shipImageName, folderPath, stats):
    start = time.time()
    saveGibImages(gibs, shipImageName, folderPath,
                  developerBackup=PARAMETERS.BACKUP_SEGMENTS_FOR_DEVELOPER)
    saveGibImagesToDiskCache(gibsWithoutMetalBits, shipImageName)
    stats['totalSaveGibImagesDuration'] += time.time() - start
    return stats


def segmentWithProfiling(PARAMETERS, baseImg, shipImageName, stats):
    start = time.time()
    gibs = segment(baseImg, shipImageName, PARAMETERS.NR_GIBS, PARAMETERS.QUICK_AND_DIRTY_SEGMENT)
    stats['totalSegmentDuration'] += time.time() - start
    return gibs, stats


def loadShipBaseImageWithProfiling(PARAMETERS, shipImageName, stats):
    start = time.time()
    baseImg, shipImageSubfolder = loadShipBaseImage(shipImageName, PARAMETERS.INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH)
    stats['totalLoadShipBaseImageDuration'] += time.time() - start
    return baseImg, shipImageSubfolder, stats


def printIterationInfo(globalStart, shipName, layoutName, shipImageName, stats):
    if (stats['nrIterations'] % 1) == 0:
        elapsedMinutes = (time.time() - globalStart) / 60.
        finishedFraction = (stats['nrIterations'] / float(stats['nrShips']))
        remainingFraction = 1. - finishedFraction
        remainingMinutes = elapsedMinutes * remainingFraction / finishedFraction
        logger.info(
            "Iterating ships: %u / %u (%.0f%%), elapsed %u minutes, remaining %u minutes, new: %u, untouched: %u, incomplete in source: %u, errors in source: %u, errors SLIC: %u, errors weaponMounts: %u, unknown errors: %u, current entry: %s / %s / %s" % (
                stats['nrIterations'], stats['nrShips'], 100. * finishedFraction, elapsedMinutes, remainingMinutes,
                stats['nrShipsWithNewlyGeneratedGibs'], stats['nrShipsWithGibsAlreadyPresent'],
                stats['nrShipsWithIncompleteGibSetup'],
                stats['nrErrorsInsource'], stats['nrErrorsInSegmentation'], stats['nrErrorsInWeaponMounts'],
                stats['nrErrorsUnknownCause'], shipName, layoutName + '.xml', shipImageName + '_base.png'))
    if (stats['nrIterations'] % 1) == 0:
        logHighestMemoryUsage()
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
            logger.info(
                "PROFILING: average profiled duration per iteration: %.3f seconds, loadShipBaseImage: %u%%, segment: %u%%, saveGibImages: %u%%, addGibEntriesToLayout: %u%%, totalSetWeaponMountGibIdsDurationPercentage: %u%%, saveShipLayout: %u%%" % (
                    (totalDuration / (stats['nrIterations'] - 1.)), totalLoadShipBaseImagePercentage,
                    totalSegmentDurationPercentage, totalSaveGibImagesDurationPercentage,
                    totalAddGibEntriesToLayoutDurationPercentage, totalSetWeaponMountGibIdsDurationPercentage,
                    totalSaveShipLayoutDurationPercentage))
