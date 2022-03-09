import sys
import collections

# Source for metadata semantics: https://www.ftlwiki.com/wiki/Modding_ships

from flow.generatorLooper import startGeneratorLoop

# note: use / instead of \ to avoid character-escaping issues
INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH = 'FTL-Multiverse 5.2.1'  # 'FTL-Multiverse 5.2.1'
ADDON_OUTPUT_FOLDERPATH = 'MV Addon GenGibs v0.9.3'  # e.g. 'MV Addon GenGibs v0.9.3'
# tutorial is part of vanilla and should have gibs. MU_COALITION_CONSTRUCTION seems to be a bug in MV, has no layout file
SHIPS_TO_IGNORE = ['PLAYER_SHIP_TUTORIAL', 'MU_COALITION_CONSTRUCTION']
# configure whether the output is meant for standalone or as an addon.
# KEEP A BACKUP READY! it is best practice to restore the backup before generating new gibs, .bat files can help a lot for that
SAVE_STANDALONE = False
SAVE_ADDON = True
# if enabled, save a separate copy of the output in gibs and/or layouts folders;
# these have to exist as subfolders of glaive and they are NOT cleaned up automatically
BACKUP_STANDALONE_SEGMENTS_FOR_DEVELOPER = False
BACKUP_STANDALONE_LAYOUTS_FOR_DEVELOPER = False

# actual number can be less: if the algorithm has an issue it is retried with fewer gibs
NR_GIBS = 5
# enable for sanity checks
QUICK_AND_DIRTY_SEGMENT = False
# enable to attach several layers of ship internals such as metal beams etc. to the gibs; takes significantly longer
GENERATE_SHIP_INTERNALS = True

# if enabled, all ships except SPECIFIC_SHIP_NAME are skipped
CHECK_SPECIFIC_SHIPS = False
SPECIFIC_SHIP_NAMES = ['MU_FED_SCOUT', 'MU_FED_SCOUT_ELITE']
# if enabled, only ITERATION_LIMIT amount of ships will be processed
LIMIT_ITERATIONS = False
ITERATION_LIMIT = 3

parameters = collections.namedtuple("parameters",
                                    """INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH ADDON_OUTPUT_FOLDERPATH SHIPS_TO_IGNORE SAVE_STANDALONE SAVE_ADDON BACKUP_STANDALONE_SEGMENTS_FOR_DEVELOPER BACKUP_STANDALONE_LAYOUTS_FOR_DEVELOPER NR_GIBS QUICK_AND_DIRTY_SEGMENT GENERATE_SHIP_INTERNALS CHECK_SPECIFIC_SHIPS SPECIFIC_SHIP_NAMES LIMIT_ITERATIONS ITERATION_LIMIT""")
coreParameters = parameters(INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH, ADDON_OUTPUT_FOLDERPATH, SHIPS_TO_IGNORE,
                            SAVE_STANDALONE, SAVE_ADDON, BACKUP_STANDALONE_SEGMENTS_FOR_DEVELOPER,
                            BACKUP_STANDALONE_LAYOUTS_FOR_DEVELOPER, NR_GIBS, QUICK_AND_DIRTY_SEGMENT,
                            GENERATE_SHIP_INTERNALS, CHECK_SPECIFIC_SHIPS, SPECIFIC_SHIP_NAMES, LIMIT_ITERATIONS,
                            ITERATION_LIMIT)


def main(argv):
    startGeneratorLoop(coreParameters)


if __name__ == '__main__':
    main(sys.argv)
