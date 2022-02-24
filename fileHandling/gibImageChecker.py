from pathlib import Path


def areGibsPresentAsImageFiles(shipImageName, sourceFolderpath):
    path = Path(sourceFolderpath + '\\img\\ships_glow\\' + shipImageName + '_gib1.png')
    if path.exists():
        return True
    path = Path(sourceFolderpath + '\\img\\ship\\' + shipImageName + '_gib1.png')
    if path.exists():
        return True
    else:
        return False
