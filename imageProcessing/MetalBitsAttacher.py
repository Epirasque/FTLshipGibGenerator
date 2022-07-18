from PIL import Image

from imageProcessing.DebugAnimator import saveGif
from imageProcessing.GibTopologizer import *
from imageProcessing.ImageProcessingUtilities import *
from imageProcessing.SeamPopulator import populateSeams

logger = logging.getLogger('GLAIVE.' + __name__)

def attachMetalBits(gibs, shipImage, tilesets, PARAMETERS, shipImageName):
    logger.debug('%s: Initializing GifFrames if applicable...' % shipImageName)
    gifFrames = initializeGifFramesWithShipImage(shipImage, PARAMETERS)
    #logger.debug('%s: Uncropping gibs...' % shipImageName)
    uncropGibs(gibs, shipImage)
    logger.debug('%s: Building seam topology...' % shipImageName)
    buildSeamTopology(gibs, shipImage  , shipImageName)
    logger.debug('%s: Ordering gibs by z-coordinates...' % shipImageName)
    gibs = orderGibsByZCoordinates(gibs)
    #logger.debug('%s: Animating Topology if applicable...' % shipImageName)
    animateTopology(gifFrames, PARAMETERS, gibs)
    #logger.debug('%s: Storing GifFrames if applicable...' % shipImageName)
    saveGif(gifFrames, shipImageName + "_topology", PARAMETERS)
    logger.debug('%s: Populating Seams...' % shipImageName)
    populateSeams(gibs, shipImageName, shipImage, tilesets, PARAMETERS)
    logger.debug('%s: Cropping and updating Gibs...' % shipImageName)
    cropAndUpdateGibs(gibs)
    logger.debug('%s: Returning...' % shipImageName)
    return gibs


def initializeGifFramesWithShipImage(shipImage, PARAMETERS):
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
