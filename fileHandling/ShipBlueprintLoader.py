import logging
import xml.etree.ElementTree as ET
from os.path import exists
import re

SHIP_BLUEPRINT_ATTRIBUTE = 'shipBlueprint'
MOD_TAG_PREFIXES = ['mod:', 'mod-append:', 'mod-overwrite:']

logger = logging.getLogger('GLAIVE.' + __name__)


def loadShipFileNames(sourceFolderpath):
    layoutUsages = {}
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
        layoutName = blueprint.attrib['layout']
        ships[blueprint.attrib['name']]['layout'] = blueprint.attrib['layout']
        if layoutName not in layoutUsages:
            layoutUsages[layoutName] = 0
        layoutUsages[layoutName] += 1
    nrSingleUsage = 0
    nrMultipleUsages = 0
    nrShipsInMultiUsage = 0
    for nr in layoutUsages.values():
        if nr == 1:
            nrSingleUsage += 1
        if nr > 1:
            nrMultipleUsages += 1
            nrShipsInMultiUsage += nr
    logger.info("Layouts with single usage: %u, with multiple usages: %u (affects %u ships)" % (nrSingleUsage, nrMultipleUsages, nrShipsInMultiUsage))
    return ships, layoutUsages


def addBlueprintsFromFile(blueprints, sourceFolderpath, filename):
    if exists(sourceFolderpath + '\\data\\' + filename) == True:
        try:
            with open(sourceFolderpath + '\\data\\' + filename, encoding='utf-8') as file:
                rawXml = file.read()
            # TODO: get rid of all <mod:...> sections
            xmlWithoutGeneralTag = re.sub(r"(<\?xml[^>]+\?>)", r"", rawXml)
            xmlWithShortenedStartCommentTag = re.sub(r"(<!-{2,})", r"<!--", xmlWithoutGeneralTag)
            xmlWithShortenedEndCommentTag = re.sub(r"(-{2,}>)", r"-->", xmlWithShortenedStartCommentTag)
            treeFormedXmlString = '<root>' + xmlWithShortenedEndCommentTag + '</root>'
            for modPrefix in MOD_TAG_PREFIXES:
                treeFormedXmlString = treeFormedXmlString.replace(modPrefix, modPrefix[:-1] + "_")
            parsed = ET.ElementTree(ET.fromstring(treeFormedXmlString))
            blueprints.extend(parsed.getroot().findall(".//" + SHIP_BLUEPRINT_ATTRIBUTE))
        except Exception as e:
            logger.exception("ERROR: Failed to parse xml content of %s: %s" % (sourceFolderpath + '\\data\\' + filename,e))
            raise e
