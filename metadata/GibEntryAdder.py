import xml.etree.ElementTree as ET

import numpy as np

LOWER_BOUND_VELOCITY = .1
UPPER_BOUND_VELOCITY = 1.5
DIRECTION_SPREAD = 20
MAXIMUM_ANGULAR_SPREAD = 1.4


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


def createGibEntry(baseHeight, baseWidth, biggestPossibleShipRadius, gib, nrGibs, shipPixelsIncludingTransparentOnes):
    gibId = gib['id']
    gibEntry = ET.Element('gib' + str(gibId))
    gibMass = gib['mass']
    gibVectorX = gib['center']['x'] - baseWidth / 2
    gibVectorY = gib['center']['y'] - baseHeight / 2
    gibVectorLength = np.linalg.norm(np.array([gibVectorX, gibVectorY]))
    normalizedDistanceFromCenter = 1. * gibVectorLength / biggestPossibleShipRadius
    relativeMass = 1. * gibMass / shipPixelsIncludingTransparentOnes
    relativeMassRegardlessOfNrGibs = relativeMass * nrGibs  # more gibs means less mass per gib -> counter that here

    addVelocityToGibEntry(gibEntry, normalizedDistanceFromCenter, relativeMassRegardlessOfNrGibs)
    addDirectionToGibEntry(gibEntry, gibVectorX, gibVectorY)
    addAngularToGibEntry(gibEntry, relativeMassRegardlessOfNrGibs)
    addCoordinatesToGibEntry(gibEntry, gib)
    return gibEntry


def addCoordinatesToGibEntry(gibEntry, gib):
    xEntry = ET.Element('x')
    xEntry.text = str(gib['x'])
    gibEntry.append(xEntry)
    yEntry = ET.Element('y')
    yEntry.text = str(gib['y'])
    gibEntry.append(yEntry)


def addAngularToGibEntry(gibEntry, relativeMassRegardlessOfNrGibs):
    angularEntry = ET.Element('angular')
    angularEntry.set("min", str(- MAXIMUM_ANGULAR_SPREAD * relativeMassRegardlessOfNrGibs / 2))
    angularEntry.set("max", str(MAXIMUM_ANGULAR_SPREAD * relativeMassRegardlessOfNrGibs / 2))
    gibEntry.append(angularEntry)


def addDirectionToGibEntry(gibEntry, gibVectorX, gibVectorY):
    # NOTE: arctan2 parameters are intentionally reversed, Y comes before X
    # NOTE: direction 0 is north, then goes counter-clockwise, not clockwise -> use minus
    mainDirection = -(round(
        np.arctan2(gibVectorY, gibVectorX) * 180. / np.pi) + 90)
    minDirection = mainDirection - round(DIRECTION_SPREAD / 2)
    maxDirection = mainDirection + round(DIRECTION_SPREAD / 2)
    minDirection = minDirection % 360
    maxDirection = maxDirection % 360
    directionEntry = ET.Element('direction')
    directionEntry.set("min", str(minDirection))
    directionEntry.set("max", str(maxDirection))
    gibEntry.append(directionEntry)


def addVelocityToGibEntry(gibEntry, normalizedDistanceFromCenter, relativeMassRegardlessOfNrGibs):
    maximumVelocity = max(min(UPPER_BOUND_VELOCITY * normalizedDistanceFromCenter / relativeMassRegardlessOfNrGibs, UPPER_BOUND_VELOCITY),
                          LOWER_BOUND_VELOCITY)
    minimalVelocity = max(maximumVelocity * 0.3, LOWER_BOUND_VELOCITY)
    velocityEntry = ET.Element('velocity')
    # TODO: determine based on mass (nr pixels) and distance to center (farther = more velocity)
    # TODO: softmax?
    velocityEntry.set("min", str(minimalVelocity))
    velocityEntry.set("max", str(maximumVelocity))
    gibEntry.append(velocityEntry)


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
