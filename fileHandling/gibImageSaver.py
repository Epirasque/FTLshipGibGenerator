import imageio

def saveGibImages(gibs, shipImageName, multiverseFolderpath):
    for gib in gibs:
        gibId = gib['id']
        imageio.imwrite(multiverseFolderpath + '\\img\\ships_glow\\' + shipImageName + '_gib' + str(gibId) + '.png')