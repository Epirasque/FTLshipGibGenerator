import collections
import sys
import logging.config
import yaml
import configparser

from flow.GeneratorLooper import *

# Source for metadata semantics: https://www.ftlwiki.com/wiki/Modding_ships

PARAMETERS = collections.namedtuple("PARAMETERS",
                                    """INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH ADDON_OUTPUT_FOLDERPATH SHIPS_TO_IGNORE OUTPUT_MODE BACKUP_SEGMENTS_FOR_DEVELOPER BACKUP_LAYOUTS_FOR_DEVELOPER NR_GIBS QUICK_AND_DIRTY_SEGMENT GENERATE_METAL_BITS ANIMATE_METAL_BITS_FOR_DEVELOPER ANIMATE_METAL_BITS_FPS CHECK_SPECIFIC_SHIPS SPECIFIC_SHIP_NAMES LIMIT_ITERATIONS ITERATION_LIMIT""")

def determineParameters():
    configParser = configparser.ConfigParser()
    configParser.read('config.ini')
    coreConfig = configParser['core']
    INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH = coreConfig.get('INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH', fallback='FTL-Multiverse 5.2.2 hotfix1')
    ADDON_OUTPUT_FOLDERPATH = coreConfig.get('ADDON_OUTPUT_FOLDERPATH', fallback='AddonWithGibs')
    ships_to_ignore_raw_string = coreConfig.get('SHIPS_TO_IGNORE', fallback='PLAYER_SHIP_TUTORIAL, MU_COALITION_CONSTRUCTION')
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
    return PARAMETERS(INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH, ADDON_OUTPUT_FOLDERPATH, SHIPS_TO_IGNORE,
                            OUTPUT_MODE, BACKUP_SEGMENTS_FOR_DEVELOPER,
                            BACKUP_LAYOUTS_FOR_DEVELOPER, NR_GIBS, QUICK_AND_DIRTY_SEGMENT,
                            GENERATE_METAL_BITS, ANIMATE_METAL_BITS_FOR_DEVELOPER, ANIMATE_METAL_BITS_FPS,
                            CHECK_SPECIFIC_SHIPS, SPECIFIC_SHIP_NAMES, LIMIT_ITERATIONS, ITERATION_LIMIT)


def main(argv):
    initializeLogging()
    logger = logging.getLogger('Core')
    logger.info('Parsing config.ini...')
    coreParameters = determineParameters()
    logger.info('Initialized core.')
    startGeneratorLoop(coreParameters)


def initializeLogging():
    print('Initializing logging...')
    with open('loggingForCore.yaml') as configFile:
        configDict = yaml.load(configFile, Loader=yaml.FullLoader)
    logging.config.dictConfig(configDict)
    print('Initialized logging.')


if __name__ == '__main__':
    main(sys.argv)
