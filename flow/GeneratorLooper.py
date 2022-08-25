import concurrent.futures
import datetime
import logging
import multiprocessing
import os
import shutil
import time
import traceback
import tracemalloc
from copy import deepcopy
from multiprocessing import current_process

import yaml

from fileHandling.CacheDao import isLayoutNameInCache, loadCacheForLayoutName, saveCacheForLayoutName
from fileHandling.GibImageChecker import areGibsPresentAsImageFiles
from fileHandling.GibImageSaver import saveGibImages, saveGibImagesToDiskCache, saveGibMetalBitsToDiskCache
from fileHandling.MetalBitsLoader import loadTilesets
from fileHandling.ProcessedShipStatsDao import countNrProcessedShipStats, storeStatsToMarkShipAsProcessed, doStatsExist, \
    STATE_FAILED, STATE_READY, clearStoredStats
from fileHandling.ShipBlueprintLoader import loadShipFileNames
from fileHandling.ShipImageLoader import loadShipBaseImage
from fileHandling.ShipLayoutDao import loadShipLayout, saveShipLayoutStandalone, saveShipLayoutAsAppendFile
from fileHandling.StabilityMarkers import createMarker, deleteMarker, countNrMarkers
from flow.LoggerUtils import getSubProcessLogger
from flow.MemoryManagement import logHighestMemoryUsage
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

# TODO: configurable parameter
NR_SUBPROCESSES = multiprocessing.cpu_count() - 1
CLEAR_ALL_STATS_FOR_PROCESSED_SHIPS = True


def startGeneratorLoop(PARAMETERS):
    globalStart = time.time()
    logger.info(
        "Starting Gib generation at %s, using %u additional subprocesses, with PARAMETERS:" % (
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), NR_SUBPROCESSES))
    logger.info(PARAMETERS)
    tracemalloc.start()
    logger.info("Loading ship file names...")
    ships, layoutUsages = loadShipFileNames(PARAMETERS.INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH)
    nrStabilityMarkers = countNrMarkers()
    if nrStabilityMarkers > 0:
        logger.error(
            "\nDetected %u markers in the stabilityMarkers subfolder, \nthese markers indicate that processing these ships / layouts was interrupted. \nTo avoid corrupted data, remove any intermediate results of these ships (in case of layouts: of ALL ships (re)using that layout!) as well as the markers." % nrStabilityMarkers)
        return
    stats = {'nrShips': len(ships),
             'nrShipsWithNewlyGeneratedGibs': 0,
             'nrShipsWithGibsAlreadyPresent': 0,
             'nrShipsWithIncompleteGibSetup': 0,
             'nrErrorsInsource': 0,
             'nrErrorsInSegmentation': 0,
             'nrErrorsInWeaponMounts': 0,
             'nrErrorsUnknownCause': 0,
             'totalLoadShipBaseImageDuration': 0,
             'totalSegmentDuration': 0,
             'totalSaveGibImagesDuration': 0,
             'totalAddGibEntriesToLayoutDuration': 0,
             'totalSetWeaponMountGibIdsDuration': 0,
             'totalSaveShipLayoutDuration': 0}
    finalStats = deepcopy(stats)
    logger.info("Cleaning up gibCache...")
    try:
        shutil.rmtree('gibCache')
    except OSError as e:
        logger.info("Did not clean gibCache (e.g. folder was already cleaned up): %s" % e)
    except Exception as e:
        logger.warning("EXCEPTION when cleaning up gibCache: %s" % e)
    if CLEAR_ALL_STATS_FOR_PROCESSED_SHIPS == True:
        logger.info("Cleaning up statsForProcessedShips...")
        clearStoredStats()
    tilesets = {}
    if (PARAMETERS.GENERATE_METAL_BITS == True):
        tilesets = loadTilesets(PARAMETERS)
    logger.info("Iterating ships...")
    futures = []
    nrSubmissions = 0
    nrPreviouslyFinishedSubmissions = countNrProcessedShipStats()
    logger.info("Already processed in previous runs: %u" % nrPreviouslyFinishedSubmissions)
    firstOfMultipleLayoutUsages = {}
    with concurrent.futures.ProcessPoolExecutor(max_workers=NR_SUBPROCESSES) as executor:
        for shipName, shipMetadata in ships.items():
            if PARAMETERS.LIMIT_ITERATIONS == True and nrSubmissions >= PARAMETERS.ITERATION_LIMIT:
                logger.info("Reached iteration limit of %u" % PARAMETERS.ITERATION_LIMIT)
                break
            # TODO: separate step for multiused layouts
            # cleanUpMemory()
            if PARAMETERS.CHECK_SPECIFIC_SHIPS == True:
                if shipName not in PARAMETERS.SPECIFIC_SHIP_NAMES:
                    # logger.debug("Skipping %s (not in whitelist)" % shipName)
                    continue
            if shipName in PARAMETERS.SHIPS_TO_IGNORE:
                logger.debug("Skipping %s (is in blacklist)" % shipName)
                continue
            shipType = shipMetadata['type']
            layoutName = shipMetadata['layout']
            if doStatsExist(shipName) == True:
                logger.debug("Skipping %s because it was processed in previous run" % shipName)
                continue

            # TODO: TEMPORARY!
            # if layoutUsages[layoutName] == 1:
            #    logger.debug("SKIPPING BECAUSE TEMPORARILY EXCLUDE SINGLE-LAYOUT-USAGE-SHIPS!")
            #    continue
            if layoutUsages[layoutName] > 1:
                if layoutName in firstOfMultipleLayoutUsages:
                    logger.debug(
                        "Skipping %s due to multiple layout usage (first usage is already in progress)" % shipName)
                    continue
                else:
                    firstOfMultipleLayoutUsages[layoutName] = True
            shipImageName = shipMetadata['img']
            # printIterationInfo(globalStart, shipName, layoutName, shipImageName, stats)
            logger.debug("Submitting %s..." % shipName)
            nrSubmissions += 1
            futures.append(
                executor.submit(processShipInParallel, PARAMETERS, shipType, layoutName, layoutUsages[layoutName],
                                shipImageName, shipName, ships, deepcopy(stats), tilesets))
            logger.debug("Submitted %s" % shipName)

            # TODO
            # if PARAMETERS.LIMIT_ITERATIONS == True and stats['nrIterations'] >= PARAMETERS.ITERATION_LIMIT:
            #    break

        phaseStart = time.time()
        nrFinishedSubmissions = 0
        nrShips = len(ships)
        while (nrFinishedSubmissions < nrSubmissions):
            nrFinishedSubmissions = countNrProcessedShipStats() - nrPreviouslyFinishedSubmissions

            elapsedMinutes = (time.time() - phaseStart) / 60.
            finishedFraction = (nrFinishedSubmissions / nrSubmissions)
            remainingFraction = 1. - finishedFraction
            if finishedFraction == 0:
                remainingMinutes = -1  # unknown
            else:
                remainingMinutes = elapsedMinutes * remainingFraction / finishedFraction
            globalElapsedMinutes = (time.time() - globalStart) / 60.

            logger.info(
                "SINGLE-LAYOUT-USAGES: Generated in this phase: %u / %u, %.0f%%, %u min elapsed, %u min remaining. (Total elapsed: %u min; Including previous run: %u / %u; Total ships: %u))" % (
                    nrFinishedSubmissions, nrSubmissions, 100. * finishedFraction, elapsedMinutes,
                    remainingMinutes, nrFinishedSubmissions + nrPreviouslyFinishedSubmissions,
                    globalElapsedMinutes, nrSubmissions + nrPreviouslyFinishedSubmissions, nrShips))
            # TODO: iterate through multi-layout ships here?
            time.sleep(5)

        for future in concurrent.futures.as_completed(futures):
            # TODO: offset by 1?

            shipName, layoutName, shipImageName, statsFromParallel = future.result()
            # TODO: also account for previously computed stuff; ensure interruptions cause no issue (already stored gibs before stats are written)
            logger.debug("Finished %s in parallel" % shipName)
            finalStats['nrShipsWithNewlyGeneratedGibs'] += statsFromParallel['nrShipsWithNewlyGeneratedGibs']
            finalStats['nrShipsWithGibsAlreadyPresent'] += statsFromParallel['nrShipsWithGibsAlreadyPresent']
            finalStats['nrShipsWithIncompleteGibSetup'] += statsFromParallel['nrShipsWithIncompleteGibSetup']
            finalStats['nrErrorsInsource'] += statsFromParallel['nrErrorsInsource']
            finalStats['nrErrorsInSegmentation'] += statsFromParallel['nrErrorsInSegmentation']
            finalStats['nrErrorsInWeaponMounts'] += statsFromParallel['nrErrorsInWeaponMounts']
            finalStats['nrErrorsUnknownCause'] += statsFromParallel['nrErrorsUnknownCause']
            finalStats['totalLoadShipBaseImageDuration'] += statsFromParallel['totalLoadShipBaseImageDuration']
            finalStats['totalSegmentDuration'] += statsFromParallel['totalSegmentDuration']
            finalStats['totalSaveGibImagesDuration'] += statsFromParallel['totalSaveGibImagesDuration']
            finalStats['totalAddGibEntriesToLayoutDuration'] += statsFromParallel[
                'totalAddGibEntriesToLayoutDuration']
            finalStats['totalSetWeaponMountGibIdsDuration'] += statsFromParallel[
                'totalSetWeaponMountGibIdsDuration']
            finalStats['totalSaveShipLayoutDuration'] += statsFromParallel['totalSaveShipLayoutDuration']

            finalStats['nrIterations'] = nrFinishedSubmissions
            printIterationInfo(globalStart, shipName, layoutName, shipImageName, finalStats)
            logger.debug("Finished recording stats for %s" % shipName)

        logger.info('Finished all initial submissions, resuming with layout re-usages.')
        futures = []
        nrSubmissions = 0
        nrPreviouslyFinishedSubmissions = countNrProcessedShipStats()
        phaseStart = time.time()

        for shipName, shipMetadata in ships.items():
            if PARAMETERS.LIMIT_ITERATIONS == True and nrSubmissions >= PARAMETERS.ITERATION_LIMIT:
                logger.info("Reached iteration limit of %u" % PARAMETERS.ITERATION_LIMIT)
                break
            # TODO: separate step for multiused layouts
            # cleanUpMemory()
            if PARAMETERS.CHECK_SPECIFIC_SHIPS == True:
                if shipName not in PARAMETERS.SPECIFIC_SHIP_NAMES:
                    # logger.debug("Skipping %s (not in whitelist)" % shipName)
                    continue
            if shipName in PARAMETERS.SHIPS_TO_IGNORE:
                logger.debug("Skipping %s (is in blacklist)" % shipName)
                continue
            layoutName = shipMetadata['layout']
            if doStatsExist(shipName) == True:
                logger.debug("Skipping %s because it was processed in previous run" % shipName)
                continue
            if layoutUsages[layoutName] <= 1:
                logger.error(
                    "Skipping %s as it is not a layout reusing ship; should not occur in this stage!" % shipName)
                continue
            shipImageName = shipMetadata['img']
            # printIterationInfo(globalStart, shipName, layoutName, shipImageName, stats)
            logger.debug("Submitting %s..." % shipName)
            nrSubmissions += 1
            futures.append(
                executor.submit(processShipInParallel, PARAMETERS, shipType, layoutName, layoutUsages[layoutName],
                                shipImageName, shipName, ships, deepcopy(stats), tilesets))
            # just delete all layout markers at very end? deleteMarker('LAYOUT_%s_started' % layoutName)
            logger.debug("Submitted %s" % shipName)

            # TODO
            # if PARAMETERS.LIMIT_ITERATIONS == True and stats['nrIterations'] >= PARAMETERS.ITERATION_LIMIT:
            #    break

        nrFinishedSubmissions = 0
        nrShips = len(ships)
        # TODO: this is not correct yet: layout reusages are not counted here
        while (nrFinishedSubmissions < nrSubmissions):
            nrFinishedSubmissions = countNrProcessedShipStats() - nrPreviouslyFinishedSubmissions
            elapsedMinutes = (time.time() - phaseStart) / 60.
            finishedFraction = (nrFinishedSubmissions / nrShips)
            remainingFraction = 1. - finishedFraction
            if finishedFraction == 0:
                remainingMinutes = -1  # unknown
            else:
                remainingMinutes = elapsedMinutes * remainingFraction / finishedFraction
            globalElapsedMinutes = (time.time() - globalStart) / 60.

            logger.info(
                "MULTIPLE-LAYOUT-USAGES: Generated in this phase: %u / %u, %.0f%%, %u min elapsed, %u min remaining. (Total elapsed: %u min; Including previous run: %u / %u; Total ships: %u)" % (
                    nrFinishedSubmissions, nrSubmissions, 100. * finishedFraction, elapsedMinutes,
                    remainingMinutes, nrFinishedSubmissions + nrPreviouslyFinishedSubmissions,
                    globalElapsedMinutes, nrSubmissions + nrPreviouslyFinishedSubmissions, nrShips))

            # TODO: iterate through multi-layout ships here?
            time.sleep(5)

        logger.info('Finished all processes, shutting down Executors.')
    logger.debug('Iterating finished futures...')
    for future in concurrent.futures.as_completed(futures):
        # TODO: offset by 1?

        shipName, layoutName, shipImageName, statsFromParallel = future.result()
        # TODO: also account for previously computed stuff; ensure interruptions cause no issue (already stored gibs before stats are written)
        logger.debug("Finished %s in parallel" % shipName)
        finalStats['nrShipsWithNewlyGeneratedGibs'] += statsFromParallel['nrShipsWithNewlyGeneratedGibs']
        finalStats['nrShipsWithGibsAlreadyPresent'] += statsFromParallel['nrShipsWithGibsAlreadyPresent']
        finalStats['nrShipsWithIncompleteGibSetup'] += statsFromParallel['nrShipsWithIncompleteGibSetup']
        finalStats['nrErrorsInsource'] += statsFromParallel['nrErrorsInsource']
        finalStats['nrErrorsInSegmentation'] += statsFromParallel['nrErrorsInSegmentation']
        finalStats['nrErrorsInWeaponMounts'] += statsFromParallel['nrErrorsInWeaponMounts']
        finalStats['nrErrorsUnknownCause'] += statsFromParallel['nrErrorsUnknownCause']
        finalStats['totalLoadShipBaseImageDuration'] += statsFromParallel['totalLoadShipBaseImageDuration']
        finalStats['totalSegmentDuration'] += statsFromParallel['totalSegmentDuration']
        finalStats['totalSaveGibImagesDuration'] += statsFromParallel['totalSaveGibImagesDuration']
        finalStats['totalAddGibEntriesToLayoutDuration'] += statsFromParallel['totalAddGibEntriesToLayoutDuration']
        finalStats['totalSetWeaponMountGibIdsDuration'] += statsFromParallel['totalSetWeaponMountGibIdsDuration']
        finalStats['totalSaveShipLayoutDuration'] += statsFromParallel['totalSaveShipLayoutDuration']

        finalStats['nrIterations'] = nrFinishedSubmissions
        logger.debug("Finished recording stats for %s" % shipName)

    logger.info('Cleaning up LAYOUT markers...')
    for layoutName in firstOfMultipleLayoutUsages.keys():
        deleteMarker('LAYOUT_started_%s' % layoutName)

    logger.info(
        "DONE. Created gibs for %u ships out of %u ships, %u of which had gibs before, %u of which had an incomplete gib setup. \nErrors when loading source: %u. Failed ship segmentations: %u. Ships with unassociated weaponMounts: %u. Unknown errors: %u" % (
            finalStats['nrShipsWithNewlyGeneratedGibs'], finalStats['nrShips'],
            finalStats['nrShipsWithGibsAlreadyPresent'],
            finalStats['nrShipsWithIncompleteGibSetup'], finalStats['nrErrorsInsource'],
            finalStats['nrErrorsInSegmentation'],
            finalStats['nrErrorsInWeaponMounts'], finalStats['nrErrorsUnknownCause']))
    logger.info("Cleaning up gibCache...")
    try:
        shutil.rmtree('gibCache')
    except OSError as e:
        logger.info("Did not clean gibCache (e.g. folder was already cleaned up): %s" % e)
    except Exception:
        logger.warning("UNEXPECTED EXCEPTION when cleaning up gibCache: %s" % traceback.format_exc())
    logger.info('Total runtime in minutes: %u' % ((time.time() - globalStart) / 60))


def processShipInParallel(PARAMETERS, shipType, layoutName, nrLayoutUsages, shipImageName, shipName, ships, stats,
                          tilesets):
    # print('Initializing logging for %u...' % os.getpid())
    process = current_process()
    process.name = shipName
    status = STATE_FAILED
    with open('loggingForSubprocess.yaml') as configFile:
        configDict = yaml.load(configFile, Loader=yaml.FullLoader)
    logging.config.dictConfig(configDict)
    logger = getSubProcessLogger()
    # print('Initialized logging for %u.' % os.getpid())
    logger.debug('Running subprocess %u in parallel for %s' % (os.getpid(), shipName))
    createMarker('SHIP_started_%s' % shipName)
    if nrLayoutUsages > 1:
        createMarker('LAYOUT_started_%s' % layoutName)
    layout = loadShipLayout(layoutName, PARAMETERS.INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH)
    if layout == None:
        logger.error('Cannot process layout for %s ' % shipName)
        stats['nrErrorsInsource'] += 1
    elif hasShipGibs(PARAMETERS, layout, shipImageName):
        logger.debug('Skipping ship that already has gibs')
        stats['nrShipsWithGibsAlreadyPresent'] += 1
        status = STATE_READY
    else:
        stats, status = createNewGibs(PARAMETERS, shipType, layout, layoutName,
                                      shipName, shipImageName, ships, stats, tilesets)
    storeStatsToMarkShipAsProcessed(shipName, stats, status)
    deleteMarker('SHIP_started_%s' % shipName)
    logger.debug('Finishing subprocess %u' % os.getpid())
    return shipName, layoutName, shipImageName, stats


def createNewGibs(PARAMETERS, shipType, layout, layoutName, name, shipImageName, ships, stats, tilesets):
    logger = getSubProcessLogger()
    status = STATE_FAILED
    foundGibsSameLayout = False
    gibs = []
    folderPath = 'not set'
    if isLayoutNameInCache(layoutName) == True:
        logger.debug('Found layout already filled in this run')
        shipImageNameInCache, nrGibs, layout = loadCacheForLayoutName(layoutName)
    if areGibsPresentInLayout(layout) == True:
        foundGibsSameLayout, gibs, newGibsWithoutMetalBits, folderPath = attemptGeneratingGibsFromIdenticalLayout(
            PARAMETERS, layout, layoutName, name, shipImageName, ships, stats)
    if foundGibsSameLayout == True:
        logger.debug("Succeeded in generating gibs with mask of gibs from same layout")
        stats = saveGibImagesWithProfiling(PARAMETERS, gibs, newGibsWithoutMetalBits, shipImageName, folderPath, stats)
        status = STATE_READY
    else:
        if areGibsPresentAsImageFiles(shipImageName, PARAMETERS.INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH) == True:
            stats['nrShipsWithIncompleteGibSetup'] += 1
            logger.debug("There are gib-images for base image %s, but no layout entries in %s for it." % (
                shipImageName, layoutName))
        try:
            stats, gibs, shipImageSubfolder, layoutWithNewGibs = generateGibsForShip(PARAMETERS, shipType, layout,
                                                                                     layoutName,
                                                                                     shipImageName, stats, tilesets)
            saveCacheForLayoutName(layoutName, shipImageName, len(gibs), layoutWithNewGibs)
            logger.debug("Succeeded in generating gibs from scratch")
            status = STATE_READY
        except Exception:
            logger.error("UNEXPECTED EXCEPTION: %s" % traceback.format_exc())
            stats['nrErrorsUnknownCause'] += 1
    return stats, status


def attemptGeneratingGibsFromIdenticalLayout(PARAMETERS, layout, layoutName, name, shipImageName, ships, stats):
    logger = getSubProcessLogger()
    stats['nrShipsWithIncompleteGibSetup'] += 1  # TODO: separate profiling / stat case
    logger.debug("There are gibs in layout %s, but no images %s_gibN for it." % (layoutName, shipImageName))
    newGibsWithMetalBits = []
    newGibsWithoutMetalBits = []
    folderPath = 'not set'
    foundGibsSameLayout = False
    try:
        logger.debug('Trying to find gibs already existing for the layout before this run...')
        targetFolderPath = determineTargetFolderPath(PARAMETERS)
        shipType = ships[shipImageName]['type']
        if shipType == 'BOSS':
            nrGibs = PARAMETERS.NR_GIBS_BOSS
        elif shipType == 'PLAYER':
            nrGibs = PARAMETERS.NR_GIBS_PLAYER
        else:
            nrGibs = PARAMETERS.NR_GIBS_NORMAL_ENEMY
        foundGibsSameLayout, newGibsWithMetalBits, newGibsWithoutMetalBits, folderPath = generateGibsBasedOnSameLayoutGibMask(
            PARAMETERS, layout, layoutName, name, nrGibs, shipImageName, ships,
            PARAMETERS.INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH, targetFolderPath)
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


def generateGibsForShip(PARAMETERS, shipType, layout, layoutName, shipImageName, stats, tilesets):
    logger = getSubProcessLogger()
    baseImg, shipImageSubfolder, stats = loadShipBaseImageWithProfiling(PARAMETERS, shipImageName, stats)
    logger.debug('Segmenting %s into individual Gibs...' % shipImageName)
    gibs, stats = segmentWithProfiling(PARAMETERS, shipType, baseImg, shipImageName, stats)
    if PARAMETERS.GENERATE_METAL_BITS == True:
        logger.debug('Attaching metalbits to %s...' % shipImageName)
        gibs, uncroppedGibsWithoutMetalBits = attachMetalBits(gibs, baseImg, tilesets, PARAMETERS, shipImageName)
    else:
        uncroppedGibsWithoutMetalBits = deepcopy(gibs)
    if len(gibs) == 0:
        stats['nrErrorsInSegmentation'] += 1
    else:
        targetFolderPath = determineTargetFolderPath(PARAMETERS)
        targetFolderPath += '\\img\\' + shipImageSubfolder
        stats = saveGibImagesWithProfiling(PARAMETERS, gibs, uncroppedGibsWithoutMetalBits, shipImageName,
                                           targetFolderPath,
                                           stats)
        layoutWithNewGibs, appendContentString, stats = addGibEntriesToLayoutWithProfiling(gibs, layout, stats,
                                                                                           PARAMETERS)
        appendContentString, nrWeaponMountsWithoutGibId, stats = setWeaponMountGibIdsWithProfiling(gibs,
                                                                                                   layoutWithNewGibs,
                                                                                                   appendContentString,
                                                                                                   stats)
        if nrWeaponMountsWithoutGibId > 0:
            stats['nrErrorsInWeaponMounts'] += 1
        stats = saveShipLayoutWithProfiling(PARAMETERS, layoutName, layoutWithNewGibs, appendContentString, stats)
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


def addGibEntriesToLayoutWithProfiling(gibs, layout, stats, PARAMETERS):
    start = time.time()
    layoutWithNewGibs = addGibEntriesToLayout(layout, gibs, PARAMETERS)
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


def saveGibImagesWithProfiling(PARAMETERS, gibs, uncroppedGibsWithoutMetalBits, shipImageName, folderPath, stats):
    start = time.time()
    saveGibImages(gibs, shipImageName, folderPath,
                  developerBackup=PARAMETERS.BACKUP_SEGMENTS_FOR_DEVELOPER)
    saveGibImagesToDiskCache(uncroppedGibsWithoutMetalBits, shipImageName)
    if PARAMETERS.GENERATE_METAL_BITS == True:
        try:
            saveGibMetalBitsToDiskCache(gibs, shipImageName)
        except:
            # TODO: is this fine?
            pass
    stats['totalSaveGibImagesDuration'] += time.time() - start
    return stats


def segmentWithProfiling(PARAMETERS, shipType, baseImg, shipImageName, stats):
    start = time.time()
    gibs = segment(shipType, baseImg, shipImageName, PARAMETERS)
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
        if finishedFraction == 0:
            remainingMinutes = -1  # unknown
        else:
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
