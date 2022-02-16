import imageio


def saveGibImages(gibs, shipImageName, shipImageSubfolder, folderPath, developerBackup):
    for gib in gibs:
        gibId = gib['id']
        imageio.imwrite(
            folderPath + '\\img\\' + shipImageSubfolder + '\\' + shipImageName + '_gib' + str(gibId) + '.png',
            gib['img'])
        if developerBackup == True:
            imageio.imsave('gibs/' + shipImageName + '_gib_' + str(gibId) + '.png', gib['img'])
