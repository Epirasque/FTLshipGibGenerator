import xml.etree.ElementTree as ET


# TODO:
# in .append to add (without overwriting)
# <mod:findLike type="explosion">
#	<mod-append:gib1><x>-24</x></mod-append:gib1>
# </mod:findLike>
# note: overwrite might leave some previous ones remaining e.g. when nr_gibs=3 but that should not be an issue right?

def convertLayoutToAppendContent(layout):
    appendString = ''

    ftlNode = layout.find('FTL')
    if ftlNode == None:
        explosionNode = layout.find('explosion')
    else:
        explosionNode = ftlNode.find('explosion')

    for gibId in range(1, 10 + 1):
        gibNode = explosionNode.find('gib%u' % gibId)
        # TODO: verify this is not needed, assumption is overwriting is sufficient (assumption nrGibs >= already existing gibs in files)
        #        if gibNode == None:
        #            appendString += '<mod:findLike type="explosion">\n'
        #            appendString += '\t<mod:findLike type="gib%u">\n' % gibId
        #            appendString += '\t\t<mod:removeTag>\n'
        #            appendString += '\t</mod:findLike>\n'
        #            appendString += '</mod:findLike>\n'
        if gibNode != None:
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
            appendString += '<mod:findLike type="explosion">\n'
            appendString += '\t<mod-overwrite:gib%u>\n' % gibId
            appendString += '\t\t<velocity  min="%s" max="%s" />\n' % (velocityMin, velocityMax)
            appendString += '\t\t<direction min="%s" max="%s" />\n' % (directionMin, directionMax)
            appendString += '\t\t<angular   min="%s" max="%s" />\n' % (angularMin, angularMax)
            appendString += '\t\t<x>%s</x>\n' % (xValue)
            appendString += '\t\t<y>%s</y>\n' % (yValue)
            appendString += '\t</mod-overwrite:gib%u>\n' % gibId
            appendString += '</mod:findLike>\n'

    return appendString
