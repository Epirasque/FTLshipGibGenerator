# GLAIVE v0.9: Pre-Generate Ship Debris For Faster Than Light (FTL) Mods

# What Does It Do? (TL;DR)
Pointed to a mod directory it looks for ships that have no gibs, meaning ships that disappear the moment you destroy them. 

Generates gibs for each ship, based on the base image of the ship. Also updates the metadata (the layout xml file) for the ship. 

In standalone-mode (recommended): saves the output directly in the input folder meaning you can pack the addon again and use it right away. **Keep a separate backup of your mod before running the generator!**

In addon-mode: saves the output as a separate addon (this is the mode used for the GenGibs addon that provides gibs for vanilla Multiverse). 

# How Can I Run It?

You need to install Python 3.8 as well as the appropriate libraries that are used. 
I personally use the PyCharm Community Edition IDE, it makes loading additional libraries much easier (the IDE offers it as quick fix recommendations).  

Set the appropriate parameters in `core.py`, e.g. you can change the desired `NR_GIBS`. At very least you have to set the `INPUT_AND_STANDALONE_OUTPUT_FOLDERPATH`. Read the comments above the parameters for more details. 
Afterwards just run the main method without any additional arguments. 

## Recommended Workflow
Have two copies of your unpacked addon folder:

1. A backup from which you can restore a clean state
2. A directory which will contain the output

Keep developing your addon in 1. until it is ready for a new release. Then overwrite 2. with the contents of 1. Then run the Gib Generator against 2. If something goes wrong, fix the issue, overwrite 2. with the contents of 1. and run the Gib Generator again until you are happy with the result. 
Finally, compress 2. into a `.zip` or `.ftl` and it is ready to be delivered; but please test it first, just in case. 

You can use scripts to speed this up. I personally use `.bat` files which you can also find in this repository, you can use them as a template by adjusting the folderpaths inside. 
Please try to properly understand them and double check what you are doing because mistakes might cause you to accidentally overwrite or delete data! 

## Recommended Order Of Patching In The Slipstream Mod Manager
For Multiverse addons:
1. Multiverse
2. GenGibs
3. Your Multiverse addon with its own generated gibs

## Speeding Things Up
Check the settings in `core.py` on how to run the Gib Generator much more quickly, e.g. for a sanity check or debugging purposes. 


# How does it work?
## Program Flow
Given the path to an unpacked FTL mod, the generator will look for the following files in the `data` subfolder:
* `blueprints.xml.append`
* `autoBlueprints.xml.append`
* `bosses.xml.append` 

For each of those files found, it will look for all `shipBlueprint` entries and remember the `layout` and the `image` names from there. 
This provides a list of candidate ships for gib generation. 

First, the `layout` will be loaded. 
A candidate will be skipped if it already has gib entries in its `layout` as well as existing `_gib` images (if either is missing they will be replaced/updated). 

Next, the `_base` image of the ship will be loaded. It is used as input for the segmentation algorithm. 
That algorithm outputs the gib images including additional information such as coordinates and pixel-mass. 

Those gib images are then saved next to the `_base` image. 

Next, the explosion gib metadata is added to the layout. This outputs the updated layout as well as the `appendContentString` that contains the same changes in a Slipstream-Advanced-XML separate-mod format (see Slipstreams' `readme_modders.txt`) which is used for the generator's addon mode.

Afterwards, the layout and the `appendContentString` are further extended by also setting the proper gib ID for the ship's weapon mounts.

Finally, the metadata is saved. 

## Gib Generation
### Image Processing
#### The Underlying Segmentation Algorithm
This section explains the actual algorithm that is used to segment the `_base` image into several `_gib` images. 
The SLIC algorithm used can be found [here](https://scikit-image.org/docs/dev/api/skimage.segmentation.html#skimage.segmentation.slic). 
To understand how it works detail, read up on the [K-Means clustering algorithm](https://en.wikipedia.org/wiki/K-means_clustering). 

To explain it for people allergic to math: a parameter `k` is chosen to determine how many clusters should be formed. 
In our case, `k` is the desired number of gibs per ship and the clusters each consist of multiple pixels of the `_base` ship image. 
The clusters start at random points of the image and the algorithm tries to converge in a way that forms these clusters as compact (spherical) as possible. 
SLIC uses K-Means, but it does not only cluster accross space but also accross the color space. The `compactness` parameter weights these two aspects against each other. 
A high `compactness` value tries to form clusters as spherical as possible, whereas a low `compactness` value puts more emphasis on grouping pixels together that are of similar color. 
In our case, this usually results in gibs that are reasonably blob-ish while occasionally extending along more natural edges in the ship image. 

#### How SLIC Is Used In The Generator
As a pre-processing step, all transparent pixels are filtered out to avoid having clusters starting on them. 

The Generator tries to find a solution with a `compactness` parameter that is as low as possible in order to make the gibs look more interesting. 

The Generators applies the SLIC algorithm until the output consists of an amount of segments that is equal to `NR_GIBS`. 
If this number is not reached, it retries running the algorithm with a higher `compactness` value until it does, or until it a certain number of attempts is reached. 
If the latter is the case it will continue with the last result it has computed, which means fewer segments than was actually defined in `NR_GIBS`. 

The resulting segments are cropped and stored as gibs. Each gib also remembers its relative coordinates (before cropping) as well as its ID, center and mass. 
The mass is currently approximated as the width and height of the gib image (while there are ways to counting the individual pixels relatively fast, it still adds up quickly).

### Metadata Processing
#### Gib Velocity
The velocity (speed in the given direction) of a gib consists of a minimum and a maximum value. Whenever the ship is destroyed, FTL will pick a random value within that range.

The maximum velocity is computed by the distance from the ship center to the center of the gib divided by the mass of the gib. The idea is that a gib in the center will move 
slower than a gib on the edge. Additionally, bigger gibs will move more slowly than smaller gibs. 

The distance from center to center is normalized, meaning it is divided by (half) of the overall ship image diagonal so that bigger ships don't have surprisingly faster gibs in their outer area compared to smaller ships. 
The mass of the gib is also normalized by dividing it by all pixels in the ship image and multiplying it by the number of gibs in the ship. 
The idea is to have a similar overall look regardless of the ship size and regardless of the amount of gibs used. 
The maximum velocity is limited by lower and upper bounds. 

The minimum velocity is 30% of the maximum velocity, it is also limited by a lower bound. 

#### Gib Direction
The direction of a gib consists of a minimum and a maximum value. Whenever the ship is destroyed, FTL will pick a random value within that range. 

The direction is derived from the vector pointing from the center of the ship to the center of the gib, meaning all gibs fly away from the center of the ship. 
Additionally, a spread of 40° is applied meaning the minimum value is 20° smaller and the maximum value is 20° bigger than the calculated direction. 

#### Gib Angular
The angular (rotation speed) of a gib consists of a minimum and a maximum value. Whenever the ship is destroyed, FTL will pick a random value within that range. 

The angular value is simply determined as a random value in a spread of 1.4, meaning it reaches from -0.7 to +0.7. 

#### Gib IDs For Weapon Mounts
Weapon mounts have x and y coordinates. A challenge here is that these coordinates are not always inside the ship image. 
For each weapon mount, all gibs are checked wether the coordinates overlap with them. 
If that is not the case, the search radius around the initial weapon mount coordinates is increased by one (think of a square made of 8 pixels). 
This is repeated until a maximum radius of 500 is reached; the biggest known radius needed so far for Multiverse was 140. 

# What Is Planned For The Future?
In arbitrary order, *no promises if or when these will be done*:
- More tweaking of direction, velocity and angular values
- Ship-insides attached to the gibs (metal beams and such); this will need some effort and the final quality is hard to predict as of this writing, but I at least have a decent plan on how to implement this
- Additional debris-pieces independend from the ship image (think Flak projectiles), also added to ships with already existing gibs (there will definately be a way to turn that off as it does not look like standard FTL gibs anymore)
- Resolving remaining TODOs in the code
- Provide a compiled version that runs without installing Python

# How Can I Contact The Author Or Otherwise Get Involved?

Write to Epirasque in the [FTL: Multiverse public discord server](https://discord.gg/UTuxGNSb), I'm looking forward to your feedback and suggestions. 

If you have something that should be discussed with more people (e.g. if you have strong feelings about how the gibs' physics should behave) then use the [the-shipyard channel](https://discord.gg/Q9FaGZQw) for now. 
