ASSUMED_MAXIMUM_NUMBER_OF_GIBS_IN_LAYOUTS = 10


def areGibsPresentInLayout(layout):
    # TODO: check gib images instead of metadata? yes if addon
    explosionNode = getExplosionNode(layout)
    if explosionNode == None:
        return False

    gibsArePresent = False
    for gibId in range(1, ASSUMED_MAXIMUM_NUMBER_OF_GIBS_IN_LAYOUTS + 1):
        gibNode = explosionNode.find('gib%u' % gibId)
        if gibNode != None:
            gibsArePresent = True
            break
    return gibsArePresent


def getExplosionNode(layout):
    ftlNode = layout.find('FTL')
    if ftlNode == None:
        explosionNode = layout.find('explosion')
    else:
        explosionNode = ftlNode.find('explosion')
    return explosionNode
