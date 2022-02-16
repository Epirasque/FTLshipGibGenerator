import xml.etree.ElementTree as ET


def areGibsPresentInLayout(layout):
    # TODO: check gib images instead of metadata? yes if addon
    ftlNode = layout.find('FTL')
    if ftlNode == None:
        explosionNode = layout.find('explosion')
    else:
        explosionNode = ftlNode.find('explosion')
    if explosionNode == None:
        return False

    gibsArePresent = False
    for gibId in range(1, 6 + 1):
        gibNode = explosionNode.find('gib%u' % gibId)
        if gibNode != None:
            gibsArePresent = True
            break
    return gibsArePresent
