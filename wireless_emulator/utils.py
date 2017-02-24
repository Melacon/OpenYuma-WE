import os
import logging

logger = logging.getLogger(__name__)

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

def ensureRoot():
    if os.getuid() != 0:
        print("##### OpenYumaWE should be run as root #####")
        exit(1)

def printErrorAndExit():
    print("#### There were errors when starting the emulator. Stopping...\n")
    exit(1)

def addCoreDefaultValuesToNode(node, uuidValue):
    uuid = node.find('uuid')
    uuid.text = uuidValue
    elem = node.find('local-id/value-name')
    elem.text = "vLocalId"
    elem = node.find('local-id/value')
    elem.text = uuidValue
    elem = node.find('name/value-name')
    elem.text = "vName"
    elem = node.find('name/value')
    elem.text = uuidValue
    elem = node.find('label/value-name')
    elem.text = "vLabel"
    elem = node.find('label/value')
    elem.text = uuidValue
    elem = node.find('extension/value-name')
    elem.text = "vExtension"
    elem = node.find('extension/value')
    elem.text = uuidValue
    elem = node.find('operational-state')
    elem.text = "ENABLED"
    elem = node.find('administrative-control')
    elem.text = "UNLOCK"
    elem = node.find('administrative-state')
    elem.text = "UNLOCKED"
    elem = node.find('lifecycle-state')
    elem.text = "INSTALLED"
