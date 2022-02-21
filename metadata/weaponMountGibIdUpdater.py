# <mod:findLike type="weaponMounts">
#	<mod:findLike type="mount">
#		<mod:selector x="399" y="166" />
#		<mod:setAttributes gib="666" />
#	</mod:findLike>
# </mod:findLike>
MAX_SEARCH_RADIUS = 500 #biggest known: 140, results in 2 bugged ships (maybe: same as errors when loading multiverse data? no...)


def setWeaponMountGibIdsAsAppendContent(gibs, layoutWithNewGibs):
    appendString = '\n'
    nrWeaponMountsWithoutGibId = 0

    ftlNode = layoutWithNewGibs.find('FTL')
    if ftlNode == None:
        weaponMountsNode = layoutWithNewGibs.find('weaponMounts')
    else:
        weaponMountsNode = ftlNode.find('weaponMounts')

    for mount in weaponMountsNode:
        exactMountX = int(mount.attrib['x'])
        exactMountY = int(mount.attrib['y'])
        mountGibId = -1
        for additionalSearchRadius in range(0, MAX_SEARCH_RADIUS + 1):
            if mountGibId != -1:
                if additionalSearchRadius > 1:
                    print("Found gib association for weapon mount at search radius %d" % (additionalSearchRadius - 1))
                break
            for xDelta in range(-additionalSearchRadius, additionalSearchRadius + 1):
                for yDelta in range(-additionalSearchRadius, additionalSearchRadius + 1):
                    if liesOnBoundingBoxWithRadius(additionalSearchRadius, xDelta, yDelta):
                        mountX = exactMountX + xDelta
                        mountY = exactMountY + yDelta
                        for gib in gibs:
                            img = gib['img']
                            mountXinsideGibImage = mountX - gib['x']
                            mountYinsideGibImage = mountY - gib['y']
                            if mountXinsideGibImage >= 0 and mountXinsideGibImage < img.shape[1] \
                                    and mountYinsideGibImage >= 0 and mountYinsideGibImage < img.shape[0]:
                                mountPixelInImage = img[mountYinsideGibImage, mountXinsideGibImage]
                                if mountPixelInImage[3] != 0:
                                    #if mountGibId != -1:
                                        #print("Weapon mount x=%d, y=%d fits to multiple gibIds" % (
                                        #exactMountX, exactMountY))
                                    mountGibId = gib['id']
                                    break
        if mountGibId == -1:
            print("Weapon mount x=%d, y=%d could not be associated with a gibId" % (exactMountX, exactMountY))
            nrWeaponMountsWithoutGibId += 1
        mount.attrib[id] = mountGibId
        appendString += '<mod:findLike type="weaponMounts">\n'
        appendString += '\t<mod:findLike type="mount">\n'
        appendString += '\t\t<mod:selector x="%u" y="%u" />\n' % (exactMountX, exactMountY)
        appendString += '\t<mod:setAttributes gib="%d" />\n' % mountGibId
        appendString += '\t</mod:findLike>\n'
        appendString += '</mod:findLike>\n'

    return appendString, nrWeaponMountsWithoutGibId


def liesOnBoundingBoxWithRadius(additionalSearchRadius, xDelta, yDelta):
    return xDelta == -additionalSearchRadius or xDelta == additionalSearchRadius + 1 or yDelta == -additionalSearchRadius or yDelta == additionalSearchRadius + 1
