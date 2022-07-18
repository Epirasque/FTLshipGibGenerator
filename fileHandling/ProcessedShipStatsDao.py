import os
import pickle
import shutil

FOLDER_PATH = 'statsForProcessedShips'


def countNrProcessedShipStats():
    nrExistingFiles = 0
    for path in os.listdir(FOLDER_PATH):
        if os.path.isfile(os.path.join(FOLDER_PATH, path)):
            nrExistingFiles += 1
    return nrExistingFiles


# TODO: read actual stats for intermediate results
def storeStatsToMarkShipAsProcessed(shipImageName, stats):
    with open("%s/stats_for_%s.dictionary" % (FOLDER_PATH, shipImageName), "wb") as file:
        pickle.dump(stats, file, -1)

# TODO: use/activate (commit first...) , see shutil.rmtree('gibCache')
def clearStoredStats():
    shutil.rmtree(FOLDER_PATH)

