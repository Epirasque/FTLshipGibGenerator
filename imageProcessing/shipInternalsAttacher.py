import numpy as np
from PIL import Image

from imageProcessing.imageAnalyser import getDistanceBetweenPoints
from imageProcessing.imageCropper import cropImage


def attachShipInternals(gibs, shipImage, tilesets):
    uncropGibs(gibs, shipImage)

    centerMostGibId = getCenterMostGibId(gibs, shipImage)

    cropAndUpdateGibs(gibs)

    return gibs


def cropAndUpdateGibs(gibs):
    for gib in gibs:
        croppedGibArray, center, minX, minY = cropImage(gib['img'])
        # TODO: reenable, but its slow nrVisiblePixels = sum(matchingSegmentIndex.flatten() == True)

        gib['img'] = croppedGibArray
        gib['center'] = center
        gib['x'] = minX
        gib['y'] = minY
        oldMass = gib['mass']
        newMass = (center['x'] - minX) * (center['y'] - minY) * 4  # TODO: reenable nrVisiblePixels
        # assume ship internals only have half of the mass as normal gib pixels
        gib['mass'] = round((newMass + oldMass) / 2)


def uncropGibs(gibs, shipImage):
    for gib in gibs:
        croppedGib = Image.fromarray(gib['img'])
        uncroppedGib = Image.fromarray(np.zeros(shipImage.shape, dtype=np.uint8))
        uncroppedGib.paste(croppedGib, (gib['x'], gib['y']), croppedGib)
        gib['img'] = np.asarray(uncroppedGib)


def getCenterMostGibId(gibs, shipImage):
    shipCenter = shipImage.shape[0] / 2, shipImage.shape[1] / 2
    centerMostGibId = gibs[0]['id']
    upperBound = shipCenter[0] * shipCenter[1]
    closestDistanceToCenter = upperBound
    for gib in gibs:
        distanceToCenter = getDistanceBetweenPoints(gib['center']['x'], gib['center']['y'], shipCenter[1],
                                                    shipCenter[0])
        if distanceToCenter < closestDistanceToCenter:
            centerMostGibId = gib['id']
    return centerMostGibId