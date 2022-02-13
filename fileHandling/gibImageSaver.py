import imageio


def saveGibImages(gibs, shipImageName, shipImageSubfolder, multiverseFolderpath):
    for gib in gibs:
        gibId = gib['id']
        imageio.imwrite(
            multiverseFolderpath + '\\img\\' + shipImageSubfolder + '\\' + shipImageName + '_gib' + str(gibId) + '.png',
            gib['img'])
