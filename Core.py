import collections
import sys
import logging.config
import yaml

from flow.GeneratorLooper import *

# Source for metadata semantics: https://www.ftlwiki.com/wiki/Modding_ships

# note: use / instead of \ to avoid character-escaping issues
INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH = 'FTL-Multiverse 5.2.2 hotfix1'  # 'FTL-Multiverse 5.2.2 hotfix1'
ADDON_OUTPUT_FOLDERPATH = 'MV Addon GenGibs v0.9.5'  # e.g. 'MV Addon GenGibs v0.9.3'
# tutorial is part of vanilla and should have gibs. MU_COALITION_CONSTRUCTION seems to be a bug in MV, has no layout file
SHIPS_TO_IGNORE = ['PLAYER_SHIP_TUTORIAL', 'MU_COALITION_CONSTRUCTION']

# configure whether the output is meant for standalone or as an addon by setting OUTPUT_MODE to one of them
# KEEP A BACKUP READY! it is best practice to restore the backup before generating new gibs, .bat files can help a lot for that
OUTPUT_MODE = STANDALONE_MODE
#OUTPUT_MODE = ADDON_MODE
# configure whether the output is meant for standalone or as an addon.
# KEEP A BACKUP READY! it is best practice to restore the backup before generating new gibs, .bat files can help a lot for that

# if enabled, save a separate copy of the output in gibs and/or layouts folders;
# these have to exist as subfolders of glaive and they are NOT cleaned up automatically
BACKUP_STANDALONE_SEGMENTS_FOR_DEVELOPER = False
BACKUP_STANDALONE_LAYOUTS_FOR_DEVELOPER = False

# actual number can be less: if the algorithm has an issue it is retried with fewer gibs
NR_GIBS = 5
# enable for sanity checks
QUICK_AND_DIRTY_SEGMENT = False
# enable to attach several layers of metal bits to the gibs; takes significantly longer. THIS IS WORK IN PROGRESS!
GENERATE_METAL_BITS = False
# create gifs to illustrate the metal bit generation process into metalBitsDebugAnimations folder
ANIMATE_METAL_BITS_FOR_DEVELOPER = False
# playback speed of the gifs in frames per second
ANIMATE_METAL_BITS_FPS = 5.

# if enabled, all ships except SPECIFIC_SHIP_NAME are skipped
CHECK_SPECIFIC_SHIPS = False
SPECIFIC_SHIP_NAMES = ['MU_SLAVER_REBEL_TRANSPORT']
# if enabled, only ITERATION_LIMIT amount of ships will be processed
LIMIT_ITERATIONS = False
ITERATION_LIMIT = 3

PARAMETERS = collections.namedtuple("PARAMETERS",
                                    """INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH ADDON_OUTPUT_FOLDERPATH SHIPS_TO_IGNORE OUTPUT_MODE BACKUP_STANDALONE_SEGMENTS_FOR_DEVELOPER BACKUP_STANDALONE_LAYOUTS_FOR_DEVELOPER NR_GIBS QUICK_AND_DIRTY_SEGMENT GENERATE_METAL_BITS ANIMATE_METAL_BITS_FOR_DEVELOPER ANIMATE_METAL_BITS_FPS CHECK_SPECIFIC_SHIPS SPECIFIC_SHIP_NAMES LIMIT_ITERATIONS ITERATION_LIMIT""")
coreParameters = PARAMETERS(INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH, ADDON_OUTPUT_FOLDERPATH, SHIPS_TO_IGNORE,
                            OUTPUT_MODE, BACKUP_STANDALONE_SEGMENTS_FOR_DEVELOPER,
                            BACKUP_STANDALONE_LAYOUTS_FOR_DEVELOPER, NR_GIBS, QUICK_AND_DIRTY_SEGMENT,
                            GENERATE_METAL_BITS, ANIMATE_METAL_BITS_FOR_DEVELOPER, ANIMATE_METAL_BITS_FPS,
                            CHECK_SPECIFIC_SHIPS, SPECIFIC_SHIP_NAMES, LIMIT_ITERATIONS, ITERATION_LIMIT)


def main(argv):
    initializeLogging()
    logger = logging.getLogger('Core')
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
