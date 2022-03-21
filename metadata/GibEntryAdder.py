import numpy as np

from metadata.GibEntryCreator import createGibEntry


def addGibEntriesToLayout(layout, gibs):
    explosionNode, imgNode = getNodes(layout)
    removeOldGibs(explosionNode)
    addGibEntries(explosionNode, gibs, imgNode)
    return layout


def addGibEntries(explosionNode, gibs, imgNode):
    baseWidth = int(imgNode.attrib['w'])
    baseHeight = int(imgNode.attrib['h'])
    shipPixelsIncludingTransparentOnes = baseWidth * baseHeight
    biggestPossibleShipRadius = np.linalg.norm(np.array([baseWidth, baseHeight])) / 2
    nrGibs = len(gibs)

    for gib in gibs:
        gibEntry = createGibEntry(baseHeight, baseWidth, biggestPossibleShipRadius, gib, nrGibs,
                                  shipPixelsIncludingTransparentOnes)
        explosionNode.append(gibEntry)
        # TODO: proper linebreaks for new entries in xml file


def removeOldGibs(explosionNode):
    oldGibNodes = []
    for childNode in explosionNode:
        if childNode.tag[0:3] == "gib":
            oldGibNodes.append(childNode)
    for oldGibNode in oldGibNodes:
        explosionNode.remove(oldGibNode)


def getNodes(layout):
    ftlNode = layout.find('FTL')
    if ftlNode == None:
        imgNode = layout.find('img')
    else:
        imgNode = ftlNode.find('img')
    if ftlNode == None:
        explosionNode = layout.find('explosion')
    else:
        explosionNode = ftlNode.find('explosion')
    return explosionNode, imgNode
