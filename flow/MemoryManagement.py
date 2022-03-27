import gc
import logging
import tracemalloc

logger = logging.getLogger('GLAIVE.' + __name__)

ENABLE_LOGGING_OUTPUT = False
NR_OBJECT_TYPES_TO_OUTPUT_SORTED_BY_BIGGEST = 2

def logHighestMemoryUsage():
    if ENABLE_LOGGING_OUTPUT == True:
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('lineno')
        logger.debug("Highest memory usage:")
        for stat in top_stats[:NR_OBJECT_TYPES_TO_OUTPUT_SORTED_BY_BIGGEST]:
            logger.debug(stat)

def cleanUpMemory():
    gc.collect()
