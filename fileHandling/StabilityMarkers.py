import os
from pathlib import Path

FOLDER_PATH = 'stabilityMarkers'

def createMarker(name):
    Path('%s/%s.marker' % (FOLDER_PATH, name)).touch()

def deleteMarker(name):
    os.remove('%s/%s.marker' % (FOLDER_PATH, name))

def doesMarkerExist(name):
    file = Path('%s/%s.marker' % (FOLDER_PATH, name))
    return file.is_file()
