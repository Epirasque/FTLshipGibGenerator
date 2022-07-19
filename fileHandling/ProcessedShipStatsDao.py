import os
import pickle
import shutil
from pathlib import Path

FOLDER_PATH = 'statsForProcessedShips'

STATE_READY = 'READY'
STATE_FAILED = 'FAILED'

def countNrProcessedShipStats():
    nrExistingFiles = 0
    for path in os.listdir(FOLDER_PATH):
        if os.path.isfile(os.path.join(FOLDER_PATH, path)):
            nrExistingFiles += 1
    return nrExistingFiles - 1


# TODO: read actual stats for intermediate results
def storeStatsToMarkShipAsProcessed(shipName, stats, status):
    with open("%s/stats_for_%s_%s.dictionary" % (FOLDER_PATH, status, shipName), "wb") as file:
        pickle.dump(stats, file, -1)


def doStatsExist(shipName):
    statFileReady = Path("%s/stats_for_%s_%s.dictionary" % (FOLDER_PATH, STATE_READY, shipName))
    statFileFailed = Path("%s/stats_for_%s_%s.dictionary" % (FOLDER_PATH, STATE_FAILED, shipName))
    return statFileReady.is_file() or statFileFailed.is_file()


# TODO: use/activate (commit first...) , see shutil.rmtree('gibCache')
def clearStoredStats():
    shutil.rmtree(FOLDER_PATH)
