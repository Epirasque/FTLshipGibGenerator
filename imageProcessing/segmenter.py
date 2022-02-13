from skimage.segmentation import slic
import imageio
import numpy as np

def segment():
    img = imageio.imread('mup_engi_a_base.png')
    for nr_gibs in range(2+1, 6+1):
        transparency_mask = (img[:,:,3] != 0)
        segments = slic(img, n_segments=nr_gibs, compactness=0.7, max_num_iter=10, mask=transparency_mask)

        for gib_id in range(1, nr_gibs+1):
            print('processing gib %u of %u' % (gib_id, nr_gibs))
            idx = (segments == gib_id)
            gib = np.zeros(img.shape, dtype=np.uint8)
            gib[idx] = img[idx]
            imageio.imsave('gibs/gib_total_of_' + str(nr_gibs) + '_part_' + str(gib_id) + '.png', gib)