import gc
import tracemalloc

from flow.LoggerUtils import getSubProcessLogger

ENABLE_LOGGING_OUTPUT = False
NR_OBJECT_TYPES_TO_OUTPUT_SORTED_BY_BIGGEST = 2

def logHighestMemoryUsage():
    logger = getSubProcessLogger()
    if ENABLE_LOGGING_OUTPUT == True:
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('lineno')
        logger.debug("Highest memory usage:")
        for stat in top_stats[:NR_OBJECT_TYPES_TO_OUTPUT_SORTED_BY_BIGGEST]:
            logger.debug(stat)

# TODO: check situation for multiprocess case
def cleanUpMemory():
    gc.collect()
