import os

import imageio
from PIL import Image

from imageProcessing.GibTopologizer import *
from imageProcessing.ImageProcessingUtilities import *
from imageProcessing.SeamPopulator import populateSeams


def attachMetalBits(gibs, shipImage, tilesets, PARAMETERS, shipImageName):
    gifFrames = initialGifImageArray(PARAMETERS, shipImage)
    uncropGibs(gibs, shipImage)
    buildSeamTopology(gibs, shipImage)
    gibs = orderGibsByZCoordinates(gibs)
    animateTopology(gifFrames, PARAMETERS, gibs)
    populateSeams(gibs, shipImage, tilesets, gifFrames, PARAMETERS)
    cropAndUpdateGibs(gibs)
    saveGif(gifFrames, shipImageName, PARAMETERS)
    return gibs


def saveGif(gifFrames, shipImageName, PARAMETERS):
    if PARAMETERS.ANIMATE_METAL_BITS_FOR_DEVELOPER == True:
        filePath = '../metalBitsDebugAnimations/%s.gif' % shipImageName
        if os.path.exists(filePath):
            os.remove(filePath)
        imageio.mimwrite(filePath, gifFrames, format='GIF', fps=PARAMETERS.ANIMATE_METAL_BITS_FPS)
        # TODO: smaller filesize using pygifsicle.optimize(filePath)


def initialGifImageArray(PARAMETERS, shipImage):
    gifFrames = []
    if PARAMETERS.ANIMATE_METAL_BITS_FOR_DEVELOPER == True:
        gifFrames.append(np.asarray(shipImage, dtype=np.uint8))
    return gifFrames


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
        # assume metal bits only have half of the mass as normal gib pixels
        gib['mass'] = round((newMass + oldMass) / 2)


def uncropGibs(gibs, shipImage):
    for gib in gibs:
        croppedGib = Image.fromarray(gib['img'])
        uncroppedGib = Image.fromarray(np.zeros(shipImage.shape, dtype=np.uint8))
        uncroppedGib.paste(croppedGib, (gib['x'], gib['y']), croppedGib)
        gib['img'] = np.asarray(uncroppedGib)
