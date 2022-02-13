import xml.etree.ElementTree as ET

def areGibsPresent(layout):
    explosionNode = layout.find('explosion')
    if explosionNode == None:
        return False

    gibsArePresent = False
    for gibId in range(1, 6+1):
        gibNode = explosionNode.find('gib%u' % gibId)
        if gibNode != None:
            gibsArePresent = True
            break
    return gibsArePresent