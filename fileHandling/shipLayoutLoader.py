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
