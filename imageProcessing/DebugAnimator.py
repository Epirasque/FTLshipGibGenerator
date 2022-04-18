import os

import imageio
import numpy as np


def saveGif(gifFrames, filename, PARAMETERS):
    if PARAMETERS.ANIMATE_METAL_BITS_FOR_DEVELOPER == True:
        os.makedirs('metalBitsDebugAnimations/', exist_ok=True)
        filePath = 'metalBitsDebugAnimations/%s.gif' % filename
        if os.path.exists(filePath):
            os.remove(filePath)
        finalFrameToRecognizeEndOfGif = np.zeros(gifFrames[0].shape, dtype=np.uint8)
        gifFrames.append(finalFrameToRecognizeEndOfGif)
        imageio.mimwrite(filePath, gifFrames, format='GIF', fps=PARAMETERS.ANIMATE_METAL_BITS_FPS)
        # TODO: smaller filesize using pygifsicle.optimize(filePath)
