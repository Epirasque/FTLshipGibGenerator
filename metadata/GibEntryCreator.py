import xml.etree.ElementTree as ET

import numpy as np
from numpy import degrees

def createGibEntry(baseHeight, baseWidth, biggestPossibleShipRadius, gib, nrGibs, shipPixelsIncludingTransparentOnes, PARAMETERS):
    gibId = gib['id']
    gibEntry = ET.Element('gib' + str(gibId))
    gibMass = gib['mass']
    gibVectorX = gib['center']['x'] - baseWidth / 2.
    gibVectorY = gib['center']['y'] - baseHeight / 2.
    gibVectorLength = np.linalg.norm(np.array([gibVectorX, gibVectorY]))
    normalizedDistanceFromCenter = 1. * gibVectorLength / biggestPossibleShipRadius
    relativeMass = 1. * gibMass / shipPixelsIncludingTransparentOnes
    relativeMassRegardlessOfNrGibs = relativeMass * nrGibs  # more gibs means less mass per gib -> counter that here

    addVelocityToGibEntry(gibEntry, normalizedDistanceFromCenter, relativeMassRegardlessOfNrGibs, PARAMETERS)
    addDirectionToGibEntry(gibEntry, gibVectorX, gibVectorY, PARAMETERS)
    addAngularToGibEntry(gibEntry, relativeMassRegardlessOfNrGibs, PARAMETERS)
    addCoordinatesToGibEntry(gibEntry, gib)
    return gibEntry


def addCoordinatesToGibEntry(gibEntry, gib):
    xEntry = ET.Element('x')
    xEntry.text = str(gib['x'])
    gibEntry.append(xEntry)
    yEntry = ET.Element('y')
    yEntry.text = str(gib['y'])
    gibEntry.append(yEntry)


def addAngularToGibEntry(gibEntry, relativeMassRegardlessOfNrGibs, PARAMETERS):
    angularEntry = ET.Element('angular')
    angularEntry.set("min", str(- PARAMETERS.MAXIMUM_ANGULAR_SPREAD_IN_DEGREES / (relativeMassRegardlessOfNrGibs * 2.)))
    angularEntry.set("max", str(PARAMETERS.MAXIMUM_ANGULAR_SPREAD_IN_DEGREES / (relativeMassRegardlessOfNrGibs * 2.)))
    gibEntry.append(angularEntry)


def addDirectionToGibEntry(gibEntry, gibVectorX, gibVectorY, PARAMETERS):
    # NOTE: arctan2 PARAMETERS are INTENTIONALLY reversed, Y comes before X
    # NOTE: direction 0 is north, then goes counter-clockwise, not clockwise -> use minus
    mainDirection = -(round(
        np.arctan2(gibVectorY, gibVectorX) * 180. / np.pi) + 90)
    minDirection = mainDirection - round(PARAMETERS.TOTAL_DIRECTION_SPREAD_IN_DEGREES / 2)
    maxDirection = mainDirection + round(PARAMETERS.TOTAL_DIRECTION_SPREAD_IN_DEGREES / 2)
    if PARAMETERS.IMPLODE == True:
        minDirection += 180
        maxDirection += 180
    minDirection = minDirection % 360
    maxDirection = maxDirection % 360
    # this can happen when 'overflowing' north due to spread
    if minDirection > maxDirection:
        minDirection -= 360
    directionEntry = ET.Element('direction')
    directionEntry.set("min", str(minDirection))
    directionEntry.set("max", str(maxDirection))
    gibEntry.append(directionEntry)


def addVelocityToGibEntry(gibEntry, normalizedDistanceFromCenter, relativeMassRegardlessOfNrGibs, PARAMETERS):
    if PARAMETERS.IMPLODE == True:
        maximumVelocity = max(min(PARAMETERS.IMPLODE_SPEED_FACTOR * PARAMETERS.UPPER_BOUND_VELOCITY * normalizedDistanceFromCenter, PARAMETERS.UPPER_BOUND_VELOCITY),
                              PARAMETERS.LOWER_BOUND_VELOCITY)
        minimalVelocity = maximumVelocity
    else:
        maximumVelocity = max(
               min(PARAMETERS.UPPER_BOUND_VELOCITY * normalizedDistanceFromCenter / relativeMassRegardlessOfNrGibs,
                   PARAMETERS.UPPER_BOUND_VELOCITY),
               PARAMETERS.LOWER_BOUND_VELOCITY)
        minimalVelocity = max(maximumVelocity * 0.3, PARAMETERS.LOWER_BOUND_VELOCITY)

    velocityEntry = ET.Element('velocity')
    # TODO: determine based on mass (nr pixels) and distance to center (farther = more velocity)
    # TODO: softmax?
    velocityEntry.set("min", str(minimalVelocity))
    velocityEntry.set("max", str(maximumVelocity))
    gibEntry.append(velocityEntry)
