import collections
import sys
import logging.config

import configparser

from flow.GeneratorLooper import *

# Source for metadata semantics: https://www.ftlwiki.com/wiki/Modding_ships

PARAMETERS = collections.namedtuple("PARAMETERS",
                                    """INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH ADDON_OUTPUT_FOLDERPATH SHIPS_TO_IGNORE OUTPUT_MODE BACKUP_SEGMENTS_FOR_DEVELOPER BACKUP_LAYOUTS_FOR_DEVELOPER NR_GIBS QUICK_AND_DIRTY_SEGMENT GENERATE_METAL_BITS ANIMATE_METAL_BITS_FOR_DEVELOPER ANIMATE_METAL_BITS_FPS CHECK_SPECIFIC_SHIPS SPECIFIC_SHIP_NAMES LIMIT_ITERATIONS ITERATION_LIMIT     IMPLODE IMPLODE_SPEED_FACTOR LOWER_BOUND_VELOCITY UPPER_BOUND_VELOCITY TOTAL_DIRECTION_SPREAD_IN_DEGREES MAXIMUM_ANGULAR_SPREAD_IN_DEGREES  LAYER1_ANGLE_TOLERANCE_SPREAD_FOR_TILE_RANDOM_SELECTION LAYER3_ANGLE_TOLERANCE_SPREAD_FOR_TILE_RANDOM_SELECTION STARTING_COMPACTNESS COMPACTNESS_GAIN_PER_ATTEMPT COMPACTNESS_LIMIT MAXIMUM_DEVIATION_FROM_BASE_IMAGE_PERCENTAGE MINIMAL_WEIGHTED_SEGMENT_RATIO SHADING_MINIMUM_WEIGHT_OF_SHIP_COLOR_AGAINST_TILE_COLOR SHADING_MAXIMUM_WEIGHT_OF_SHIP_COLOR_AGAINST_TILE_COLOR""")


def determineParameters():
    configParser = configparser.ConfigParser()
    configParser.read('config.ini')
    coreConfig = configParser['core']
    INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH = coreConfig.get('INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH',
                                                            fallback='FTL-Multiverse 5.x')
    ADDON_OUTPUT_FOLDERPATH = coreConfig.get('ADDON_OUTPUT_FOLDERPATH', fallback='AddonWithGibs')
    ships_to_ignore_raw_string = coreConfig.get('SHIPS_TO_IGNORE',
                                                fallback='PLAYER_SHIP_TUTORIAL, MU_COALITION_CONSTRUCTION')
    SHIPS_TO_IGNORE = ships_to_ignore_raw_string.replace(' ', '').split(',')
    OUTPUT_MODE = coreConfig.get('OUTPUT_MODE', fallback=STANDALONE_MODE)
    BACKUP_SEGMENTS_FOR_DEVELOPER = coreConfig.getboolean('BACKUP_SEGMENTS_FOR_DEVELOPER', fallback=False)
    BACKUP_LAYOUTS_FOR_DEVELOPER = coreConfig.getboolean('BACKUP_LAYOUTS_FOR_DEVELOPER', fallback=False)
    NR_GIBS = coreConfig.getint('NR_GIBS', fallback=5)
    QUICK_AND_DIRTY_SEGMENT = coreConfig.getboolean('QUICK_AND_DIRTY_SEGMENT', fallback=False)
    GENERATE_METAL_BITS = coreConfig.getboolean('GENERATE_METAL_BITS', fallback=False)
    ANIMATE_METAL_BITS_FOR_DEVELOPER = coreConfig.getboolean('ANIMATE_METAL_BITS_FOR_DEVELOPER', fallback=False)
    ANIMATE_METAL_BITS_FPS = coreConfig.getfloat('ANIMATE_METAL_BITS_FPS', 5.)
    CHECK_SPECIFIC_SHIPS = coreConfig.getboolean('CHECK_SPECIFIC_SHIPS', fallback=False)
    specific_ship_names_raw_string = coreConfig.get('SPECIFIC_SHIP_NAMES', fallback='')
    SPECIFIC_SHIP_NAMES = specific_ship_names_raw_string.replace(' ', '').split(',')
    LIMIT_ITERATIONS = coreConfig.getboolean('LIMIT_ITERATIONS', fallback=False)
    ITERATION_LIMIT = coreConfig.getint('ITERATION_LIMIT', fallback=3)
    IMPLODE = coreConfig.getboolean('IMPLODE', fallback=False)
    IMPLODE_SPEED_FACTOR = coreConfig.getfloat('IMPLODE_SPEED_FACTOR', fallback=0.6)
    LOWER_BOUND_VELOCITY = coreConfig.getfloat('LOWER_BOUND_VELOCITY', fallback=.1)
    UPPER_BOUND_VELOCITY = coreConfig.getfloat('UPPER_BOUND_VELOCITY', fallback=1.5)
    TOTAL_DIRECTION_SPREAD_IN_DEGREES = coreConfig.getint('TOTAL_DIRECTION_SPREAD_IN_DEGREES', fallback=16)
    MAXIMUM_ANGULAR_SPREAD_IN_DEGREES = coreConfig.getfloat('MAXIMUM_ANGULAR_SPREAD_IN_DEGREES', fallback=1.4)
    LAYER1_ANGLE_TOLERANCE_SPREAD_FOR_TILE_RANDOM_SELECTION = coreConfig.getint(
        'LAYER1_ANGLE_TOLERANCE_SPREAD_FOR_TILE_RANDOM_SELECTION', fallback=15)
    LAYER3_ANGLE_TOLERANCE_SPREAD_FOR_TILE_RANDOM_SELECTION = coreConfig.getint(
        'LAYER3_ANGLE_TOLERANCE_SPREAD_FOR_TILE_RANDOM_SELECTION', fallback=10)
    STARTING_COMPACTNESS = coreConfig.getfloat('STARTING_COMPACTNESS', fallback=0.3)
    COMPACTNESS_GAIN_PER_ATTEMPT = coreConfig.getfloat('COMPACTNESS_GAIN_PER_ATTEMPT', fallback=0.05)
    COMPACTNESS_LIMIT = coreConfig.getfloat('COMPACTNESS_LIMIT', fallback=2.5)
    MAXIMUM_DEVIATION_FROM_BASE_IMAGE_PERCENTAGE = coreConfig.getfloat('MAXIMUM_DEVIATION_FROM_BASE_IMAGE_PERCENTAGE',
                                                                       fallback=1.)
    MINIMAL_WEIGHTED_SEGMENT_RATIO = coreConfig.getfloat('MINIMAL_WEIGHTED_SEGMENT_RATIO', fallback=.2)
    SHADING_MINIMUM_WEIGHT_OF_SHIP_COLOR_AGAINST_TILE_COLOR = coreConfig.getfloat(
        'SHADING_MINIMUM_WEIGHT_OF_SHIP_COLOR_AGAINST_TILE_COLOR', fallback=.2)
    SHADING_MAXIMUM_WEIGHT_OF_SHIP_COLOR_AGAINST_TILE_COLOR = coreConfig.getfloat(
        'SHADING_MAXIMUM_WEIGHT_OF_SHIP_COLOR_AGAINST_TILE_COLOR', fallback=.5)

    return PARAMETERS(INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH, ADDON_OUTPUT_FOLDERPATH, SHIPS_TO_IGNORE,
                      OUTPUT_MODE, BACKUP_SEGMENTS_FOR_DEVELOPER,
                      BACKUP_LAYOUTS_FOR_DEVELOPER, NR_GIBS, QUICK_AND_DIRTY_SEGMENT,
                      GENERATE_METAL_BITS, ANIMATE_METAL_BITS_FOR_DEVELOPER, ANIMATE_METAL_BITS_FPS,
                      CHECK_SPECIFIC_SHIPS, SPECIFIC_SHIP_NAMES, LIMIT_ITERATIONS, ITERATION_LIMIT,
                      IMPLODE, IMPLODE_SPEED_FACTOR, LOWER_BOUND_VELOCITY, UPPER_BOUND_VELOCITY,
                      TOTAL_DIRECTION_SPREAD_IN_DEGREES, MAXIMUM_ANGULAR_SPREAD_IN_DEGREES,
                      LAYER1_ANGLE_TOLERANCE_SPREAD_FOR_TILE_RANDOM_SELECTION,
                      LAYER3_ANGLE_TOLERANCE_SPREAD_FOR_TILE_RANDOM_SELECTION, STARTING_COMPACTNESS,
                      COMPACTNESS_GAIN_PER_ATTEMPT, COMPACTNESS_LIMIT, MAXIMUM_DEVIATION_FROM_BASE_IMAGE_PERCENTAGE,
                      MINIMAL_WEIGHTED_SEGMENT_RATIO, SHADING_MINIMUM_WEIGHT_OF_SHIP_COLOR_AGAINST_TILE_COLOR,
                      SHADING_MAXIMUM_WEIGHT_OF_SHIP_COLOR_AGAINST_TILE_COLOR)


def main(argv):
    runIt()


def runIt():
    multiprocessing.freeze_support()
    initializeLogging()
    logger = logging.getLogger('Core')
    logger.info('Parsing config.ini...')
    coreParameters = determineParameters()
    logger.info('Initialized core.')
    try:
        startGeneratorLoop(coreParameters)
    except Exception as e:
        logger.error('Stopped main execution due to Exception %s ' % e)
        pass
    logger.info('Press any key to exit...')
    os.system('pause')


def initializeLogging():
    print('Initializing logging...')
    with open('loggingForCore.yaml') as configFile:
        configDict = yaml.load(configFile, Loader=yaml.FullLoader)
    logging.config.dictConfig(configDict)
    print('Initialized logging.')


if __name__ == '__main__':
    main(sys.argv)
