import xml.etree.ElementTree as ET


def addGitEntriesToLayout(layout, gibs):
    explosionNode = layout.find('explosion')
    for gib in gibs:
        gibId = gib['id']
        gibEntry = ET.Element('gib' + str(gibId))

        velocityEntry = ET.Element('velocity')
        velocityEntry.set("min", str(0.10))
        velocityEntry.set("max", str(0.20))
        gibEntry.append(velocityEntry)

        directionEntry = ET.Element('direction')
        directionEntry.set("min", str(0))
        directionEntry.set("max", str(360))
        gibEntry.append(directionEntry)

        angularEntry = ET.Element('angular')
        angularEntry.set("min", str(-0.30))
        angularEntry.set("max", str(0.30))
        gibEntry.append(angularEntry)

        xEntry = ET.Element('x')
        xEntry.text = str(200)
        gibEntry.append(xEntry)

        yEntry = ET.Element('y')
        yEntry.text = str(60)
        gibEntry.append(yEntry)

        explosionNode.append(gibEntry)
        # TODO: proper linebreaks for new entries in xml file
    return layout
