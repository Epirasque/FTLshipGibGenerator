# note: overwrite might leave some previous ones remaining e.g. when nr_gibs=3 but that should not be an issue right?

ASSUMED_MAXIMUM_NUMBER_OF_GIBS_IN_LAYOUTS = 1000


def convertLayoutToAppendContent(layout):
    appendString = ''

    explosionNode = getExplosionNode(layout)

    for gibId in range(1, ASSUMED_MAXIMUM_NUMBER_OF_GIBS_IN_LAYOUTS + 1):
        gibNode = explosionNode.find('gib%u' % gibId)
        # TODO: verify this is not needed, assumption is overwriting is sufficient (assumption nrGibs >= already existing gibs in files)
        #        if gibNode == None:
        #            appendString += '<mod:findLike type="explosion">\n'
        #            appendString += '\t<mod:findLike type="gib%u">\n' % gibId
        #            appendString += '\t\t<mod:removeTag>\n'
        #            appendString += '\t</mod:findLike>\n'
        #            appendString += '</mod:findLike>\n'
        if gibNode != None:
            appendString += createAppendStringForGibEntry(gibId, gibNode)

    return appendString


def createAppendStringForGibEntry(gibId, gibNode):
    velocityNode = gibNode.find('velocity')
    velocityMin = velocityNode.attrib['min']
    velocityMax = velocityNode.attrib['max']
    directionNode = gibNode.find('direction')
    directionMin = directionNode.attrib['min']
    directionMax = directionNode.attrib['max']
    angularNode = gibNode.find('angular')
    angularMin = angularNode.attrib['min']
    angularMax = angularNode.attrib['max']
    xNode = gibNode.find('x')
    xValue = xNode.text
    yNode = gibNode.find('y')
    yValue = yNode.text
    gibString = ''
    gibString += '<mod:findLike type="explosion">\n'
    gibString += '\t<mod-overwrite:gib%u>\n' % gibId
    gibString += '\t\t<velocity  min="%s" max="%s" />\n' % (velocityMin, velocityMax)
    gibString += '\t\t<direction min="%s" max="%s" />\n' % (directionMin, directionMax)
    gibString += '\t\t<angular   min="%s" max="%s" />\n' % (angularMin, angularMax)
    gibString += '\t\t<x>%s</x>\n' % (xValue)
    gibString += '\t\t<y>%s</y>\n' % (yValue)
    gibString += '\t</mod-overwrite:gib%u>\n' % gibId
    gibString += '</mod:findLike>\n'
    return gibString


def getExplosionNode(layout):
    ftlNode = layout.find('FTL')
    if ftlNode == None:
        explosionNode = layout.find('explosion')
    else:
        explosionNode = ftlNode.find('explosion')
    return explosionNode
