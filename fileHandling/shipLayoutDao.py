import re
import xml.etree.ElementTree as ET


def loadShipLayout(shipLayoutName, multiverseFolderpath):
    try:
        # workaround: ElementTree expect a single root node
        with open(multiverseFolderpath + '\\data\\' + shipLayoutName + '.xml') as file:
            rawXml = file.read()
        return ET.fromstring(re.sub(r"(<\?xml[^>]+\?>)", r"\1<root>", rawXml) + "</root>")
        # return ET.parse(multiverseFolderpath + '\\data\\' + shipLayoutName + '.xml')
    except FileNotFoundError:
        print('No layout XML file found for shipBlueprint layout attribute: %s' % shipLayoutName)


def saveShipLayout(layout, shipLayoutName, multiverseFolderpath, developerBackup):
    filepath = multiverseFolderpath + '\\data\\' + shipLayoutName + '.xml'
    ET.ElementTree(layout).write(filepath, encoding='utf-8', xml_declaration=True)
    removeRootNode(filepath)
    if developerBackup == True:
        developerBackupFilepath = 'layouts/' + shipLayoutName + '.xml'
        ET.ElementTree(layout).write(developerBackupFilepath, encoding='utf-8', xml_declaration=True)
        removeRootNode(developerBackupFilepath)


def removeRootNode(filepath):
    # taken and heavily adjusted from https://pynative.com/python-delete-lines-from-file/
    with open(filepath, 'r+') as file:
        lines = file.readlines()
        file.seek(0)
        file.truncate()

        for number, line in enumerate(lines):
            writeIt = True
            if line == '<root>\n' or line == '</root>\n' or line == '</root>' or (number == 2 and line == '\n'):
                writeIt = False
            if number == 4:
                file.write("<!--Copyright (c) 2012 by Subset Games. All rights reserved.-->\n")
            if writeIt:
                file.write(line)
