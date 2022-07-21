#TODO: add remaining CRUD for cache here
import pickle
from pathlib import Path

FOLDER_PATH = 'gibCache'

def isLayoutNameInCache(layoutName):
    file = Path('%s/layout_%s.cache' % (FOLDER_PATH, layoutName))
    return file.is_file()

def loadCacheForLayoutName(layoutName):
    with open('%s/layout_%s.cache' % (FOLDER_PATH, layoutName), "rb") as file:
        dict = pickle.load(file)
    return dict['shipImageNameInCache'], dict['nrGibs'], dict['layout']

def saveCacheForLayoutName(layoutName, shipImageNameInCache, nrGibs, layout):
    dict = {}
    dict['shipImageNameInCache'], dict['nrGibs'], dict['layout'] = shipImageNameInCache, nrGibs, layout
    with open('%s/layout_%s.cache' % (FOLDER_PATH, layoutName), "wb") as file:
        pickle.dump(dict, file)