import logging
import xml.etree.ElementTree as ET
from os.path import exists
import re

SHIP_BLUEPRINT_ATTRIBUTE = 'shipBlueprint'
BOSS_SHIP_TAGNAME = 'bossShip'
PLAYER_SHIP_TAGNAME = 'ship'
FTL_TAGNAME = 'FTL'
MOD_TAG_PREFIXES = ['mod:', 'mod-append:', 'mod-overwrite:']

logger = logging.getLogger('GLAIVE.' + __name__)


def loadShipFileNames(sourceFolderpath):
    layoutUsages = {}
    ships = {}
    allBlueprints = []
    bossShipNames, playerShipNames = getShipPropertiesFromHyperspace(sourceFolderpath, 'hyperspace.xml')

    playershipBlueprints = getBlueprintsFromFile(sourceFolderpath, 'blueprints.xml')
    autoBlueprints = getBlueprintsFromFile(sourceFolderpath, 'autoBlueprints.xml')
    bossBlueprints = getBlueprintsFromFile(sourceFolderpath, 'bosses.xml')
    dlcBlueprints = getBlueprintsFromFile(sourceFolderpath, 'dlcBlueprints.xml')
    dlcOverwriteBlueprints = getBlueprintsFromFile(sourceFolderpath, 'dlcBlueprintsOverwrite.xml')

    playershipBlueprintsAppend = getBlueprintsFromFile(sourceFolderpath, 'blueprints.xml.append')
    autoBlueprintsAppend = getBlueprintsFromFile(sourceFolderpath, 'autoBlueprints.xml.append')
    bossBlueprintsAppend = getBlueprintsFromFile(sourceFolderpath, 'bosses.xml.append')
    dlcBlueprintsAppend = getBlueprintsFromFile(sourceFolderpath, 'dlcBlueprints.xml.append')
    dlcOverwriteBlueprintsAppend = getBlueprintsFromFile(sourceFolderpath, 'dlcBlueprintsOverwrite.xml.append')

    allBlueprints.extend(playershipBlueprints)
    allBlueprints.extend(autoBlueprints)
    allBlueprints.extend(bossBlueprints)
    allBlueprints.extend(dlcBlueprints)
    allBlueprints.extend(dlcOverwriteBlueprints)

    allBlueprints.extend(playershipBlueprintsAppend)
    allBlueprints.extend(autoBlueprintsAppend)
    allBlueprints.extend(bossBlueprintsAppend)
    allBlueprints.extend(dlcBlueprintsAppend)
    allBlueprints.extend(dlcOverwriteBlueprintsAppend)

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
        if blueprint.attrib['name'] in ships:
            ships[blueprint.attrib['name']]['type'] = 'PLAYER'
    for blueprint in playershipBlueprintsAppend:
        if blueprint.attrib['name'] in ships:
            ships[blueprint.attrib['name']]['type'] = 'PLAYER'
    for blueprint in bossBlueprints:
        if blueprint.attrib['name'] in ships:
            ships[blueprint.attrib['name']]['type'] = 'BOSS'
    for blueprint in bossBlueprintsAppend:
        if blueprint.attrib['name'] in ships:
            ships[blueprint.attrib['name']]['type'] = 'BOSS'

    for playerShipName in playerShipNames:
        if playerShipName in ships:
            ships[playerShipName]['type'] = 'PLAYER'
    for bossShipName in bossShipNames:
        if bossShipName in ships:
            ships[bossShipName]['type'] = 'BOSS'

    nrPlayerShips = 0
    nrBossShips = 0
    nrNormalEnemyShips = 0
    for shipName in ships:
        type = ships[shipName]['type']
        if type == 'PLAYER':
            nrPlayerShips += 1
        elif type == 'BOSS':
            nrBossShips += 1
        else:
            nrNormalEnemyShips += 1
    logger.info(
        "Layouts with single usage: %u, with multiple usages: %u (affects %u ships)" % (
            nrSingleUsage, nrMultipleUsages, nrShipsInMultiUsage))
    logger.info(
        "Ship types: %u playerships, %u bosses, %u normal enemies" % (nrPlayerShips, nrBossShips, nrNormalEnemyShips))
    return ships, layoutUsages


def getShipPropertiesFromHyperspace(sourceFolderpath, filename):
    bossShipNames = []
    playerShipNames = []
    if exists(sourceFolderpath + '\\data\\' + filename) == True:
        try:
            with open(sourceFolderpath + '\\data\\' + filename, encoding='utf-8') as file:
                rawXml = file.read()
            xmlWithoutGeneralTag = re.sub(r"(<\?xml[^>]+\?>)", r"", rawXml)
            xmlWithShortenedStartCommentTag = re.sub(r"(<!-{2,})", r"<!--", xmlWithoutGeneralTag)
            xmlWithShortenedEndCommentTag = re.sub(r"(-{2,}>)", r"-->", xmlWithShortenedStartCommentTag)
            xmlWithShortenedEmptyCommentTag = re.sub(r"<!-{2,}>", r"<!-- -->", xmlWithShortenedEndCommentTag)
            treeFormedXmlString = '<root>' + xmlWithShortenedEmptyCommentTag + '</root>'
            parsed = ET.ElementTree(ET.fromstring(treeFormedXmlString))
            bossShipNodes = parsed.getroot().findall(".//" + BOSS_SHIP_TAGNAME)
            for bossShipNode in bossShipNodes:
                bossShipNames.append(bossShipNode.text)
            playerShipNodes = parsed.getroot().findall(".//" + PLAYER_SHIP_TAGNAME)
            for playerShipNode in playerShipNodes:
                playerShipNames.append(playerShipNode.text)
        except Exception as e:
            logger.exception(
                "ERROR: Failed to parse xml content of %s: %s" % (sourceFolderpath + '\\data\\' + filename, e))
            raise e
    return bossShipNames, playerShipNames


def getBlueprintsFromFile(sourceFolderpath, filename):
    blueprints = []
    isAppend = filename.endswith('.append')
    if exists(sourceFolderpath + '\\data\\' + filename) == True:
        try:
            with open(sourceFolderpath + '\\data\\' + filename, encoding='utf-8') as file:
                rawXml = file.read()
            xmlWithoutGeneralTag = re.sub(r"(<\?xml[^>]+\?>)", r"", rawXml)
            xmlWithShortenedStartCommentTag = re.sub(r"(<!-{2,})", r"<!--", xmlWithoutGeneralTag)
            xmlWithShortenedEndCommentTag = re.sub(r"(-{2,}>)", r"-->", xmlWithShortenedStartCommentTag)
            xmlWithShortenedEmptyCommentTag = re.sub(r"<!-{2,}>", r"<!-- -->", xmlWithShortenedEndCommentTag)
            treeFormedXmlString = '<root>' + xmlWithShortenedEmptyCommentTag + '</root>'
            for modPrefix in MOD_TAG_PREFIXES:
                treeFormedXmlString = treeFormedXmlString.replace(modPrefix, modPrefix[:-1] + "_")
            parsed = ET.ElementTree(ET.fromstring(treeFormedXmlString))
            if isAppend == True:
                blueprints = parsed.getroot().findall(".//" + SHIP_BLUEPRINT_ATTRIBUTE)
            else:
                blueprints = parsed.getroot().find(FTL_TAGNAME).findall(SHIP_BLUEPRINT_ATTRIBUTE)
        except Exception as e:
            logger.exception(
                "ERROR: Failed to parse xml content of %s: %s" % (sourceFolderpath + '\\data\\' + filename, e))
            raise e
    return blueprints;
