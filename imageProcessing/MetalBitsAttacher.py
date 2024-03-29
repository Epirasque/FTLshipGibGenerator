from PIL import Image

from imageProcessing.DebugAnimator import saveGif
from imageProcessing.GibTopologizer import *
from imageProcessing.ImageProcessingUtilities import *
from imageProcessing.SeamPopulator import populateSeams


def determineShipColorMean(shipImage):
    colorMaskCoordinates = np.where(np.any(shipImage != [0, 0, 0, 0], axis=-1))
    colorPoints = shipImage[colorMaskCoordinates]
    return (np.mean(colorPoints[:,0]), np.mean(colorPoints[:,1]), np.mean(colorPoints[:,2]))


def attachMetalBits(gibs, shipImage, tilesets, PARAMETERS, shipImageName):
    gifFrames = initializeGifFramesWithShipImage(shipImage, PARAMETERS)
    uncropGibs(gibs, shipImage)
    buildSeamTopology(gibs, shipImage, shipImageName)
    gibs = orderGibsByZCoordinates(gibs)
    uncroppedGibsWithoutMetalBits = deepcopy(gibs)
    # cropGibs(gibsWithoutMetalBits)
    animateTopology(gifFrames, PARAMETERS, gibs)
    saveGif(gifFrames, shipImageName + "_topology", PARAMETERS)
    shipColorMean = determineShipColorMean(shipImage)
    populateSeams(gibs, shipImageName, shipImage, tilesets, shipColorMean, PARAMETERS)
    cropAndUpdateGibs(gibs, shipImage)
    return gibs, uncroppedGibsWithoutMetalBits


def initializeGifFramesWithShipImage(shipImage, PARAMETERS):
    gifFrames = []
    if PARAMETERS.ANIMATE_METAL_BITS_FOR_DEVELOPER == True:
        gifFrames.append(np.asarray(shipImage, dtype=np.uint8))
    return gifFrames


def cropGibs(gibs):
    for gib in gibs:
        croppedGibArray, center, minX, minY = cropImage(gib['img'])
        gib['img'] = croppedGibArray


def cropAndUpdateGibs(gibs, shipImage):
    for gib in gibs:
        croppedGibArray, center, minX, minY = cropImage(gib['img'])
        # TODO: reenable, but its slow nrVisiblePixels = sum(matchingSegmentIndex.flatten() == True)

        gib['img'] = croppedGibArray
        if 'uncropped_metalbits' not in gib:
            gib['uncropped_metalbits'] = np.zeros(shipImage.shape, dtype=np.uint8)
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
