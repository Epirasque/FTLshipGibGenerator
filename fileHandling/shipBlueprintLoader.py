import xml.etree.ElementTree as ET
from os.path import exists

SHIP_BLUEPRINT_ATTRIBUTE = 'shipBlueprint'


def loadShipFileNames(sourceFolderpath):
    blueprints = []
    if exists(sourceFolderpath + "\\data\\blueprints.xml.append") == True:
        parsed = ET.parse(sourceFolderpath + "\\data\\blueprints.xml.append")
        blueprints.extend(parsed.getroot().findall(SHIP_BLUEPRINT_ATTRIBUTE))
    if exists(sourceFolderpath + "\\data\\autoBlueprints.xml.append") == True:
        parsed = ET.parse(sourceFolderpath + "\\data\\autoBlueprints.xml.append")
        blueprints.extend(parsed.getroot().findall(SHIP_BLUEPRINT_ATTRIBUTE))
    if exists(sourceFolderpath + "\\data\\bosses.xml.append") == True:
        parsed = ET.parse(sourceFolderpath + "\\data\\bosses.xml.append")
        blueprints.extend(parsed.getroot().findall(SHIP_BLUEPRINT_ATTRIBUTE))

    ships = {}
    for blueprint in blueprints:
        ships[blueprint.attrib['name']] = {}
        ships[blueprint.attrib['name']]['img'] = blueprint.attrib['img']
        ships[blueprint.attrib['name']]['layout'] = blueprint.attrib['layout']

    return ships
