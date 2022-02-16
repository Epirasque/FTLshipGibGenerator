import imageio


def saveGibImagesStandalone(gibs, shipImageName, shipImageSubfolder, multiverseFolderpath, developerBackup):
    for gib in gibs:
        gibId = gib['id']
        imageio.imwrite(
            multiverseFolderpath + '\\img\\' + shipImageSubfolder + '\\' + shipImageName + '_gib' + str(gibId) + '.png',
            gib['img'])
        if developerBackup == True:
            imageio.imsave('gibs/' + shipImageName + '_gib_' + str(gibId) + '.png', gib['img'])
