import imageio
import os

GIB_CACHE_FOLDER = 'gibCache'


def saveGibImages(gibs, shipImageName, shipImageSubfolder, folderPath, developerBackup):
    for gib in gibs:
        gibId = gib['id']
        imageio.imwrite(
            folderPath + '\\img\\' + shipImageSubfolder + '\\' + shipImageName + '_gib' + str(gibId) + '.png',
            gib['img'])
        if developerBackup == True:
            imageio.imsave('gibs/' + shipImageName + '_gib' + str(gibId) + '.png', gib['img'])
        if not os.path.exists(GIB_CACHE_FOLDER): # TODO: refactor to avoid redundant saves
            os.makedirs(GIB_CACHE_FOLDER)
        imageio.imsave(GIB_CACHE_FOLDER + '/' + shipImageName + '_gib' + str(gibId) + '.png', gib['img'])
