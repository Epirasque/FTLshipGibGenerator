SEARCH_RADIUS_REPORT_THRESHOLD = 10
MAX_SEARCH_RADIUS = 500  # biggest known: 140, results in 2 bugged ships


def setWeaponMountGibIdsAsAppendContent(gibs, layoutWithNewGibs):
    appendString = '\n'
    nrWeaponMountsWithoutGibId = 0

    weaponMountsNode = getWeaponMountsNode(layoutWithNewGibs)

    for mount in weaponMountsNode:
        weaponMountAppendString, nrWeaponMountsWithoutGibId = generateAppendStringForWeaponMount(appendString, gibs,
                                                                                                 mount,
                                                                                                 nrWeaponMountsWithoutGibId)
        appendString += weaponMountAppendString

    return appendString, nrWeaponMountsWithoutGibId


def generateAppendStringForWeaponMount(appendString, gibs, mount, nrWeaponMountsWithoutGibId):
    exactMountX = int(mount.attrib['x'])
    exactMountY = int(mount.attrib['y'])
    mountGibId = findGibIdForWeaponMountCoordinates(exactMountX, exactMountY, gibs)
    if mountGibId == -1:
        print("Weapon mount x=%d, y=%d could not be associated with a gibId" % (exactMountX, exactMountY))
        nrWeaponMountsWithoutGibId += 1
    mount.set('gib', str(mountGibId))
    appendString += '<mod:findLike type="weaponMounts">\n'
    appendString += '\t<mod:findLike type="mount">\n'
    appendString += '\t\t<mod:selector x="%u" y="%u" />\n' % (exactMountX, exactMountY)
    appendString += '\t\t<mod:setAttributes gib="%d" />\n' % mountGibId
    appendString += '\t</mod:findLike>\n'
    appendString += '</mod:findLike>\n'
    return appendString, nrWeaponMountsWithoutGibId


def findGibIdForWeaponMountCoordinates(exactMountX, exactMountY, gibs):
    mountGibId = -1
    for additionalSearchRadius in range(0, MAX_SEARCH_RADIUS + 1):
        if mountGibId != -1:
            if additionalSearchRadius >= SEARCH_RADIUS_REPORT_THRESHOLD:
                print("Found gib association for weapon mount at search radius %d" % additionalSearchRadius)
            break
        mountGibId = findGibIdForWeaponMountInSearchRadius(additionalSearchRadius, exactMountX, exactMountY, gibs,
                                                           mountGibId)
    return mountGibId


def findGibIdForWeaponMountInSearchRadius(additionalSearchRadius, exactMountX, exactMountY, gibs, mountGibId):
    for xDelta in range(-additionalSearchRadius, additionalSearchRadius + 1):
        for yDelta in range(-additionalSearchRadius, additionalSearchRadius + 1):
            if liesOnBoundingBoxWithRadius(additionalSearchRadius, xDelta, yDelta):
                mountX = exactMountX + xDelta
                mountY = exactMountY + yDelta
                mountGibId = findGibIdAtSearchCoordinates(gibs, mountGibId, mountX, mountY)
    return mountGibId


def findGibIdAtSearchCoordinates(gibs, mountGibId, mountX, mountY):
    for gib in gibs:
        img = gib['img']
        mountXinsideGibImage = mountX - gib['x']
        mountYinsideGibImage = mountY - gib['y']
        if areCoordinatesInsideOfImageBox(img, mountXinsideGibImage, mountYinsideGibImage):
            mountPixelInImage = img[mountYinsideGibImage, mountXinsideGibImage] # yes, y is the 1st dimension
            if mountPixelInImage[3] != 0:
                # if mountGibId != -1:
                # print("Weapon mount x=%d, y=%d fits to multiple gibIds" % (
                # exactMountX, exactMountY))
                mountGibId = gib['id']
                break
    return mountGibId


def areCoordinatesInsideOfImageBox(img, mountXinsideGibImage, mountYinsideGibImage):
    return mountXinsideGibImage >= 0 and mountXinsideGibImage < img.shape[1] \
           and mountYinsideGibImage >= 0 and mountYinsideGibImage < img.shape[0]


def getWeaponMountsNode(layoutWithNewGibs):
    ftlNode = layoutWithNewGibs.find('FTL')
    if ftlNode == None:
        weaponMountsNode = layoutWithNewGibs.find('weaponMounts')
    else:
        weaponMountsNode = ftlNode.find('weaponMounts')
    return weaponMountsNode


def liesOnBoundingBoxWithRadius(additionalSearchRadius, xDelta, yDelta):
    return xDelta == -additionalSearchRadius or xDelta == additionalSearchRadius + 1 or yDelta == -additionalSearchRadius or yDelta == additionalSearchRadius + 1
