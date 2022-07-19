import os
from pathlib import Path

FOLDER_PATH = 'stabilityMarkers'

def countNrMarkers():
    nrExistingFiles = 0
    for path in os.listdir(FOLDER_PATH):
        if os.path.isfile(os.path.join(FOLDER_PATH, path)):
            nrExistingFiles += 1
    return nrExistingFiles - 1

def createMarker(name):
    Path('%s/%s.marker' % (FOLDER_PATH, name)).touch()

def deleteMarker(name):
    os.remove('%s/%s.marker' % (FOLDER_PATH, name))

def doesMarkerExist(name):
    file = Path('%s/%s.marker' % (FOLDER_PATH, name))
    return file.is_file()
