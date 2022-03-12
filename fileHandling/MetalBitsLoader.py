from PIL import Image

DEFAULT_TILESET = 'c2'
TILE_WIDTH = 144
TILE_HEIGHT = 144

def loadTilesets():
    tilesetFilePath = '../metalBits/%s.png' % DEFAULT_TILESET

    tilesets = {}
    tilesets['default'] = {}
    tilesets['default']['chunklayer1'] = []
    for k,piece in enumerate(crop(tilesetFilePath,TILE_WIDTH,TILE_WIDTH),0):
        img=Image.new('RGBA', (TILE_WIDTH,TILE_WIDTH), 255)
        img.paste(piece)
        tilesets['default']['chunklayer1'].append(img)
        #path=os.path.join('../delme',"IMG-%s.png" % k)
        #img.save(path)
    return tilesets

# taken from https://stackoverflow.com/questions/5953373/how-to-split-image-into-multiple-pieces-in-python
def crop(infile,height,width):
    im = Image.open(infile)
    imgwidth, imgheight = im.size
    for i in range(imgheight//height):
        for j in range(imgwidth//width):
            box = (j*width, i*height, (j+1)*width, (i+1)*height)
            yield im.crop(box)
