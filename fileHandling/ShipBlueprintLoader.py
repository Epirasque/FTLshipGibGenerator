import logging
import xml.etree.ElementTree as ET
from os.path import exists
import re

SHIP_BLUEPRINT_ATTRIBUTE = 'shipBlueprint'
MOD_TAG_PREFIXES = ['mod:', 'mod-append:', 'mod-overwrite:']

logger = logging.getLogger('GLAIVE.' + __name__)

def loadShipFileNames(sourceFolderpath):
    blueprints = []
    addBlueprintsFromFile(blueprints, sourceFolderpath, 'blueprints.xml.append')
    addBlueprintsFromFile(blueprints, sourceFolderpath, 'autoBlueprints.xml.append')
    addBlueprintsFromFile(blueprints, sourceFolderpath, 'bosses.xml.append')
    addBlueprintsFromFile(blueprints, sourceFolderpath, 'dlcBlueprints.xml.append')
    addBlueprintsFromFile(blueprints, sourceFolderpath, 'dlcBlueprintsOverwrite.xml.append')

    ships = {}
    for blueprint in blueprints:
        ships[blueprint.attrib['name']] = {}
        ships[blueprint.attrib['name']]['img'] = blueprint.attrib['img']
        ships[blueprint.attrib['name']]['layout'] = blueprint.attrib['layout']

    return ships


def addBlueprintsFromFile(blueprints, sourceFolderpath, filename):
    if exists(sourceFolderpath + '\\data\\' + filename) == True:
        try:
            with open(sourceFolderpath + '\\data\\' + filename, encoding='utf-8') as file:
                rawXml = file.read()
            # TODO: get rid of all <mod:...> sections
            treeFormedXmlString = '<root>' + re.sub(r"(<\?xml[^>]+\?>)", r"", rawXml) + '</root>'
            for modPrefix in MOD_TAG_PREFIXES:
                treeFormedXmlString = treeFormedXmlString.replace(modPrefix, modPrefix[:-1] + "_")
            parsed = ET.ElementTree(ET.fromstring(treeFormedXmlString))
            blueprints.extend(parsed.getroot().findall(".//" + SHIP_BLUEPRINT_ATTRIBUTE))
        except:
            logger.exception("ERROR: Failed to parse xml content of " + sourceFolderpath + '\\data\\' + filename)
