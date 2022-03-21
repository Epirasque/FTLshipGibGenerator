# GLAIVE v0.9.5: Pre-Generate Ship Debris (Gibs) For Faster Than Light (FTL) Mods

# What Does It Do? (TL;DR)

Pointed to a mod directory it looks for ships that have no gibs, meaning ships that disappear the moment you destroy
them.

Generates gibs for each ship, based on the base image of the ship. Also updates the metadata (the layout xml file) for
the ship.

In standalone-mode (recommended): saves the output directly in the input folder meaning you can pack the addon again and
use it right away. **Keep a separate backup of your mod before running the generator!**

In addon-mode: saves the output as a separate addon (this is the mode used for the GenGibs addon that provides gibs for
vanilla Multiverse).

# How Can I Run It?

You need to install Python 3.8 as well as the appropriate libraries that are used. I personally use the PyCharm
Community Edition IDE, it makes loading additional libraries much easier (the IDE offers it as quick fix
recommendations).

Set the appropriate parameters in `core.py`, e.g. you can change the desired `NR_GIBS`. At very least you have to set
the `INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH`. Read the comments above the parameters for more details. Afterwards just
run the main method without any additional arguments.

## Recommended Workflow

The generator will ignore ships which already have gibs (regardless if they were drawn manually or generated). This
means you might want to always apply it to an 'ungenerated' version of your addon because once generated they will not
be overwritten anymore even if you run a new version of the generator.

Have two copies of your unpacked addon folder:

1. A backup from which you can restore a clean state
2. A directory which will contain the output

Keep developing your addon in 1. until it is ready for a new release. Then overwrite 2. with the contents of 1. Then run
the Gib Generator against 2. If something goes wrong, fix the issue, overwrite 2. with the contents of 1. and run the
Gib Generator again until you are happy with the result. Finally, compress 2. into a `.zip` or `.ftl` and it is ready to
be delivered; but please test it first, just in case.

You can use scripts to speed this up. I personally use `.bat` files which you can also find in this repository, you can
use them as a template by adjusting the folderpaths inside. Please try to properly understand them and double check what
you are doing because mistakes might cause you to accidentally overwrite or delete data!

## Recommended Order Of Patching In The Slipstream Mod Manager

For Multiverse addons:

1. Multiverse
2. GenGibs
3. Your Multiverse addon with its own generated gibs

## Speeding Things Up

Check the settings in `core.py` on how to run the Gib Generator much more quickly, e.g. for a sanity check or debugging
purposes.

# How Does It Work?

## Program Flow

### Loading Blueprints

Given the path to an unpacked FTL mod, the generator will look for the following files in the `data` subfolder:

* `blueprints.xml.append`
* `autoBlueprints.xml.append`
* `bosses.xml.append`
* `dlcBlueprints.xml.append`
* `dlcBlueprintsOverwrite.xml.append`

For each of those files found, it will look for all `shipBlueprint` entries and remember the `layout` and the `image`
names from there. This provides a list of candidate ships for gib generation.

### Loading The Ship Layout

First, the `layout` will be loaded. A candidate will be skipped if it already has gib entries in its `layout` as well as
existing `_gib` images (if either is missing they will be replaced/updated).

### Dealing With Layouts That Are Used Multiple Times

If the `layout` already has gib entries, it is an indication that it is used more than once: ships can use the same
layout but a different image, this makes sense if the shape and weapon mounts remain the same but the ship has a
different color schema. To address this, a cache is checked to see if the generator already made gibs for this `layout`
before. This cache is located in the `gibCache` folder of this project, an in-memory attempt had exceeded certain
limits. If the cache contains gibs from a previously processed ship then those gibs will be used as a mask to cut out
gibs for the ship that is currently being iterated. This ensures an identical shape of gibs for the same layout, which
is necessary to match with the `x` and `y` coordinates stored in the `layout` file. If the cache does not contain an
entry, all `shipBlueprint` entries that were initially loaded are searched for an identical `layout`. If any of those is
found and already has existing gib images, then these are used for as the mask. This is the case if gibs existed before
running the generator, otherwise they would be part of the cache).

### Creating Gibs

If there are no gibs for any other ships that happen to have the same `layout`, then the `_base` image of the ship will
be loaded. It is used as input for the segmentation algorithm. That algorithm outputs the gib images including
additional information such as coordinates and pixel-mass.

Those gib images are then saved next to the `_base` image.

### Updating The Layout

Next, the explosion gib metadata is added to the layout. This outputs the updated layout as well as
the `appendContentString` that contains the same changes in a Slipstream-Advanced-XML separate-mod format (see
Slipstreams' `readme_modders.txt`) which is used for the generator's addon mode.

Afterwards, the layout and the `appendContentString` are further extended by also setting the proper gib ID for the
ship's weapon mounts.

Finally, the metadata is saved.

## Gib Generation

### Image Processing

#### The Underlying Segmentation Algorithm

This section explains the actual algorithm that is used to segment the `_base` image into several `_gib` images. The
SLIC algorithm used can be
found [here](https://scikit-image.org/docs/dev/api/skimage.segmentation.html#skimage.segmentation.slic). To understand
how it works detail, read up on the [K-Means clustering algorithm](https://en.wikipedia.org/wiki/K-means_clustering).

To explain it for people allergic to math: a parameter `k` is chosen to determine how many clusters should be formed. In
our case, `k` is the desired number of gibs per ship and the clusters each consist of multiple pixels of the `_base`
ship image. The clusters start at random points of the image and the algorithm tries to converge in a way that forms
these clusters as compact (spherical) as possible. 

SLIC uses K-Means, but it does not only cluster accross space but
also accross the color space. The `compactness` parameter weights these two aspects against each other. A
high `compactness` value tries to form clusters as spherical as possible, whereas a low `compactness` value puts more
emphasis on grouping pixels together that are of similar color. In our case, this usually results in gibs that are
reasonably blob-ish while occasionally extending along more natural edges in the ship image.

#### How SLIC Is Used In The Generator

As a pre-processing step, all transparent pixels are filtered out to avoid having clusters starting on them.

The Generator tries to find a solution with a `compactness` parameter that is quite small in order to make the
gibs look more interesting.

The Generators applies the SLIC algorithm until the output consists of an amount of segments that is equal to `NR_GIBS`.
If this number is not reached, it retries running the algorithm with a higher `compactness` value until it does, or
until it a certain number of attempts is reached. There is also a rare edge-case that causes a retry, this will happen 
if an attempt to reassemble the original image by putting together the segments deviates from the original image by a 
certain percentage. 
If the maximum number of retries is reached, the generator will continue with the last result it has
computed, which means fewer segments than was actually defined in `NR_GIBS`. 

The resulting segments are cropped and stored as gibs. Each gib also remembers its relative coordinates (before
cropping) as well as its ID, center and mass. The mass is currently approximated as the width and height of the gib
image (while there are ways to counting the individual pixels relatively fast, it still adds up quickly).

### Metadata Processing

#### Gib Velocity

The velocity (speed in the given direction) of a gib consists of a minimum and a maximum value. Whenever the ship is
destroyed, FTL will pick a random value within that range.

The maximum velocity is computed by 2 times the distance from the ship center to the center of the gib, divided by the
mass of the gib. The idea is that a gib in the center will move slower than a gib on the edge. Additionally, bigger gibs
will move more slowly than smaller gibs.

The distance from center to center is normalized, meaning it is divided by (half) of the overall ship image diagonal so
that bigger ships don't have surprisingly faster gibs in their outer area compared to smaller ships. The mass of the gib
is also normalized by dividing it by all pixels in the ship image and multiplying it by the number of gibs in the ship.
The idea is to have a similar overall look regardless of the ship size and regardless of the amount of gibs used. The
maximum velocity is limited by lower and upper bounds.

The minimum velocity is 30% of the maximum velocity, it is also limited by a lower bound.

#### Gib Direction

The direction of a gib consists of a minimum and a maximum value. Whenever the ship is destroyed, FTL will pick a random
value within that range.

The direction is derived from the vector pointing from the center of the ship to the center of the gib, meaning all gibs
fly away from the center of the ship. Additionally, a spread of 16° is applied meaning the minimum value is 8° smaller
and the maximum value is 8° bigger than the calculated direction.

#### Gib Angular

The angular (rotation speed) of a gib consists of a minimum and a maximum value. Whenever the ship is destroyed, FTL
will pick a random value within that range.

The angular value is simply determined as a random value in a spread of 1.4, reaching from -0.7 to +0.7, then divided 
by the normalized mass of the gib to give smaller gibs more spin than bigger ones. 

#### Gib IDs For Weapon Mounts

Weapon mounts have x and y coordinates. A challenge here is that these coordinates are not always inside the ship image.
For each weapon mount, all gibs are checked wether the coordinates overlap with them. If that is not the case, the
search radius around the initial weapon mount coordinates is increased by one (think of a square made of 8 pixels). This
is repeated until a maximum radius of 500 is reached; the biggest known radius needed so far for Multiverse was 140.

# Known Issues

- One known case of `tile cannot extend outside image` when generating

# What Is Planned For The Future?

In arbitrary order, *no promises if or when these will be done*:

- Metal bits attached to the gibs, see progress section below
- More tweaking of direction, velocity and angular values
- Additional debris-pieces independent of the ship image (think Flak projectiles), also added to ships with already
  existing gibs (there will definitely be a way to turn that off as it does not look like standard FTL gibs anymore)
- Resolving remaining TODOs in the code
- Provide a compiled version that runs without installing Python
- Avoid having longer lines sticking out of gibs (usually black lines that separate parts of the ship image)

# Progress Of Metal Bits

- [ ] tilesets
    - [x] initializing tilesets
        - [x] load and split
        - [x] detect origin/edge
        - [x] support pre-rotation
    - [ ] program flow
        - [x] feature toggle
        - [x] flow to class at lowest level
        - [ ] profiling
    - [ ] support different layers
    - [ ] support different themes
- [x] mark seams between gibs
    - [x] prototype
- [ ] innermost layer1 (chunks)
    - [ ] tileset
    - [x] determine general direction
        - [x] prototype
    - [x] constraints
        - [x] don't leave metal bit origin visible anywhere
        - [x] don't generate outside of base ship shape
        - [x] don't cover gibs with lower z-value
    - [x] iteration
- [ ] layer2
- [ ] layer3
- [ ] layer4
- [x] ensure metal bits are always hidden initially
    - [x] unit test
        - [x] update to reconstruct based on z-layers
    - [x] ensure gibs cover each other properly (edge-asymmetry/logic needed)
- [ ] QoL
    - [x] feature toggle
    - [x] save generation process as gif for debugging
    - [ ] performance improvements
- [ ] deal with re-use layout mechanism: issue differentiating core gib and internals?
- [ ] shading
- [ ] tweak until it looks great

# How Can I Contact The Author Or Otherwise Get Involved?

Write to Epirasque in the [FTL: Multiverse public discord server](https://discord.gg/UTuxGNSb), I'm looking forward to
your feedback and suggestions. My timezone is GMT+1.

If you have something that should be discussed with more people (e.g. if you have strong feelings about how the gibs'
physics should behave) then please use the [the-shipyard channel](https://discord.gg/Q9FaGZQw) for now.

# Special Thanks

- marcrusian for consulting support
- [Multiverse](https://subsetgames.com/forum/viewtopic.php?f=11&t=38203)
  and [Hyperspace](https://subsetgames.com/forum/viewtopic.php?f=11&t=35095) developers and community for feedback and
  support
- Subset games for a great game and modding foundation for it
- [Slipstream](https://subsetgames.com/forum/viewtopic.php?f=12&t=17102) for properly managing mods in general, as well
  as providing a handy addon-sandbox