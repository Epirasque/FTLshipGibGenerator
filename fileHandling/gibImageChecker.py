from pathlib import Path


def areGibsPresentAsImageFiles(shipImageName, multiverseFolderpath):
    path = Path(multiverseFolderpath + '\\img\\ships_glow\\' + shipImageName + '_gib1.png')
    if path.exists():
        return True
    path = Path(multiverseFolderpath + '\\img\\ship\\' + shipImageName + '_gib1.png')
    if path.exists():
        return True
    else:
        return False
