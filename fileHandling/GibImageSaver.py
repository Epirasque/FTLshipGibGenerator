import imageio
import os

GIB_CACHE_FOLDER = 'gibCache'


def saveGibImages(gibs, shipImageName, folderPath, developerBackup):
    for gib in gibs:
        gibId = gib['id']
        os.makedirs(folderPath, exist_ok=True)
        imageio.imwrite(
            folderPath + '\\' + shipImageName + '_gib' + str(gibId) + '.png',
            gib['img'])
        if developerBackup == True:
            os.makedirs('gibs/', exist_ok=True)
            imageio.imsave('gibs/' + shipImageName + '_gib' + str(gibId) + '.png', gib['img'])


def saveGibImagesToDiskCache(gibsWithoutMetalBits, shipImageName):
    for gib in gibsWithoutMetalBits:
        gibId = gib['id']
        # TODO: refactor to avoid redundant saves
        os.makedirs(GIB_CACHE_FOLDER, exist_ok=True)
        imageio.imsave(GIB_CACHE_FOLDER + '/' + shipImageName + '_gib' + str(gibId) + '.png', gib['img'])
