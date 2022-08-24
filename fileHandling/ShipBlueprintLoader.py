import logging
import xml.etree.ElementTree as ET
from os.path import exists
import re

SHIP_BLUEPRINT_ATTRIBUTE = 'shipBlueprint'
MOD_TAG_PREFIXES = ['mod:', 'mod-append:', 'mod-overwrite:']

logger = logging.getLogger('GLAIVE.' + __name__)


def loadShipFileNames(sourceFolderpath):
    layoutUsages = {}
    ships = {}
    allBlueprints = []
    playershipBlueprints = getBlueprintsFromFile(sourceFolderpath, 'blueprints.xml.append')
    autoBlueprints = getBlueprintsFromFile(sourceFolderpath, 'autoBlueprints.xml.append')
    bossBlueprints = getBlueprintsFromFile(sourceFolderpath, 'bosses.xml.append')
    dlcBlueprints = getBlueprintsFromFile(sourceFolderpath, 'dlcBlueprints.xml.append')
    dlcOverwriteBlueprints = getBlueprintsFromFile(sourceFolderpath, 'dlcBlueprintsOverwrite.xml.append')

    allBlueprints.extend(playershipBlueprints)
    allBlueprints.extend(autoBlueprints)
    allBlueprints.extend(bossBlueprints)
    allBlueprints.extend(dlcBlueprints)
    allBlueprints.extend(dlcOverwriteBlueprints)
    for blueprint in allBlueprints:
        ships[blueprint.attrib['name']] = {}
        ships[blueprint.attrib['name']]['type'] = 'NORMAL_ENEMY'
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

    for blueprint in playershipBlueprints:
        ships[blueprint.attrib['name']]['type'] = 'PLAYER'
    for blueprint in bossBlueprints:
        ships[blueprint.attrib['name']]['type'] = 'BOSS'

    # TODO: check hyperspace.xml for <bossShip>

    logger.info("Layouts with single usage: %u, with multiple usages: %u (affects %u ships)" % (nrSingleUsage, nrMultipleUsages, nrShipsInMultiUsage))
    return ships, layoutUsages


def getBlueprintsFromFile(sourceFolderpath, filename):
    blueprints = []
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
            blueprints = parsed.getroot().findall(".//" + SHIP_BLUEPRINT_ATTRIBUTE)
        except Exception as e:
            logger.exception("ERROR: Failed to parse xml content of %s: %s" % (sourceFolderpath + '\\data\\' + filename,e))
            raise e
    return blueprints;
