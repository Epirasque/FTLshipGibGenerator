import xml.etree.ElementTree as ET
from os.path import exists
import re

SHIP_BLUEPRINT_ATTRIBUTE = 'shipBlueprint'


def loadShipFileNames(sourceFolderpath):
    blueprints = []
    addBlueprintsFromFile(blueprints, sourceFolderpath, 'blueprints.xml.append')
    addBlueprintsFromFile(blueprints, sourceFolderpath, 'autoBlueprints.xml.append')
    addBlueprintsFromFile(blueprints, sourceFolderpath, 'bosses.xml.append')

    ships = {}
    for blueprint in blueprints:
        ships[blueprint.attrib['name']] = {}
        ships[blueprint.attrib['name']]['img'] = blueprint.attrib['img']
        ships[blueprint.attrib['name']]['layout'] = blueprint.attrib['layout']

    return ships


def addBlueprintsFromFile(blueprints, sourceFolderpath, filename):
    if exists(sourceFolderpath + '\\data\\' + filename) == True:
        with open(sourceFolderpath + '\\data\\' + filename, encoding='utf-8') as file:
            rawXml = file.read()
        # TODO: get rid of all <mod:...> sections
        validXmlString =  '<root>' + re.sub(r"(<\?xml[^>]+\?>)", r"\1", rawXml) + '</root>'
        parsed = ET.ElementTree(ET.fromstring(validXmlString))
        blueprints.extend(parsed.getroot().findall(".//" + SHIP_BLUEPRINT_ATTRIBUTE))
