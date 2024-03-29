import logging
import re
import xml.etree.ElementTree as ET
import os
from multiprocessing import current_process

# logger = logging.getLogger('GLAIVE.' + __name__)


def loadShipLayout(shipLayoutName, sourceFolderpath):
    logger = logging.getLogger('GLAIVE.' + __name__ + '|' + current_process().name)
    os.makedirs(sourceFolderpath + '\\data\\', exist_ok=True)
    try:
        # workaround: ElementTree expect a single root node
        with open(sourceFolderpath + '\\data\\' + shipLayoutName + '.xml', encoding='utf-8') as file:
            rawXml = file.read()
        return ET.fromstring(re.sub(r"(<\?xml[^>]+\?>)", r"\1<root>", rawXml) + "</root>")
        # return ET.parse(sourceFolderpath + '\\data\\' + shipLayoutName + '.xml')
    except FileNotFoundError:
        logger.error('No layout XML file found for shipBlueprint layout attribute: %s' % shipLayoutName)


def saveShipLayoutStandalone(layout, shipLayoutName, sourceFolderpath, developerBackup):
    os.makedirs(sourceFolderpath + '\\data\\', exist_ok=True)
    filepath = sourceFolderpath + '\\data\\' + shipLayoutName + '.xml'
    ET.ElementTree(layout).write(filepath, encoding='utf-8', xml_declaration=True)
    removeRootNode(filepath)
    if developerBackup == True:
        os.makedirs('layouts/', exist_ok=True)
        developerBackupFilepath = 'layouts/' + shipLayoutName + '.xml'
        ET.ElementTree(layout).write(developerBackupFilepath, encoding='utf-8', xml_declaration=True)
        removeRootNode(developerBackupFilepath)


def saveShipLayoutAsAppendFile(appendContentString, shipLayoutName, addonFolderpath, developerBackup):
    os.makedirs(addonFolderpath + '\\data\\', exist_ok=True)
    filepath = addonFolderpath + '\\data\\' + shipLayoutName + '.xml.append'
    if os.path.exists(filepath):
        os.remove(filepath)
    with open(filepath, "w") as appendFile:
        appendFile.write(appendContentString)
    if developerBackup == True:
        os.makedirs('layouts/', exist_ok=True)
        developerBackupFilepath = 'layouts/' + shipLayoutName + '.xml.append'
        with open(developerBackupFilepath, "w") as appendFile:
            appendFile.write(appendContentString)


def removeRootNode(filepath):
    # taken and heavily adjusted from https://pynative.com/python-delete-lines-from-file/
    with open(filepath, 'r+') as file:
        content = file.read()
        file.seek(0)
        content = content.replace("<root>", '').replace("</root>", '')
        file.write(content)
        file.truncate()
