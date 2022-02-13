import xml.etree.ElementTree as ET

SHIP_BLUEPRINT_ATTRIBUTE = 'shipBlueprint'

def loadShipFileNames(multiverseFolderpath):
    playerBlueprints=ET.parse(multiverseFolderpath + "\\data\\blueprints.xml.append")
    autoBlueprints=ET.parse(multiverseFolderpath + "\\data\\autoBlueprints.xml.append")
    bossBlueprints=ET.parse(multiverseFolderpath + "\\data\\bosses.xml.append")

    blueprints=playerBlueprints.getroot().findall(SHIP_BLUEPRINT_ATTRIBUTE)
    blueprints.extend(autoBlueprints.getroot().findall(SHIP_BLUEPRINT_ATTRIBUTE))
    blueprints.extend(bossBlueprints.getroot().findall(SHIP_BLUEPRINT_ATTRIBUTE))

    ships={}
    for blueprint in blueprints:
        ships[blueprint.attrib['name']] = {}
        ships[blueprint.attrib['name']]['img'] = blueprint.attrib['img']
        ships[blueprint.attrib['name']]['layout'] = blueprint.attrib['layout']

    return ships