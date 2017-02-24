import logging
import subprocess
import copy

import wireless_emulator.emulator
from wireless_emulator.utils import addCoreDefaultValuesToNode

logger = logging.getLogger(__name__)

class Interface:

    def __init__(self, intfUuid, interfaceId, ofPort, neObj):
        self.IP = None
        self.uuid = intfUuid
        self.id = interfaceId
        self.ofPort = ofPort

        self.neObj = neObj
        self.prefixName = None
        self.interfaceName = None

        self.emEnv = wireless_emulator.emulator.Emulator()

        self.MAC = self.emEnv.macAddressFactory.generateMacAddress(self.neObj.getNeId(), self.id)
        if self.MAC is None:
            logger.critical("No MAC Address created for NE=%s and interface=%s",
                            self.neObj.getNeUuid(), self.uuid)

    def getIpAddress(self):
        return self.IP

    def setIpAddress(self, IP):
        self.IP = IP

    def getInterfaceUuid(self):
        return self.uuid

    def getInterfaceName(self):
        return self.interfaceName

    def getNeName(self):
        return self.neObj.dockerName

    def getMacAddress(self):
        return self.MAC

    def buildCoreModelXml(self):
        neNode = self.neObj.networkElementXmlNode
        ltpNode = copy.deepcopy(self.neObj.ltpXmlNode)
        uuid = ltpNode.find('uuid')
        ltpUuid = "ltp-" + self.interfaceName
        uuid.text = ltpUuid
        addCoreDefaultValuesToNode(ltpNode, ltpUuid)

        lpNode = ltpNode.find('lp')
        uuid = ltpNode.find('uuid')
        lpUuid = "lp-" + self.interfaceName
        uuid.text = lpUuid
        addCoreDefaultValuesToNode(lpNode, lpUuid)

        neNode.append(ltpNode)

    def buildMicrowaveModelXml(self):
        parentNode = self.neObj.microwaveModuleXmlNode

        airInterface = copy.deepcopy(self.neObj.airInterfacePacXmlNode)
        lpUuid = "lp-" + self.interfaceName

        layerProtocol = airInterface.find('layer-protocol')
        layerProtocol.text = lpUuid

        supportedChPlan = airInterface.find(
            'air-interface-capability/supported-channel-plan-list/supported-channel-plan')
        supportedChPlan.text = "plan_1"

        trModeId = airInterface.find(
            'air-interface-capability/supported-channel-plan-list/transmission-mode-list/transmission-mode-id')
        trModeId.text = "transmission_mode_1"

        parentNode.append(airInterface)

    def buildXmlFile(self):
        self.buildCoreModelXml()
        self.buildMicrowaveModelXml()

class MwpsInterface(Interface):

    def __init__(self, intfUuid, interfaceId, ofPort, neObj):
        Interface.__init__(self, intfUuid, interfaceId, ofPort, neObj)
        self.prefixName = 'mwps-'
        self.interfaceName = self.prefixName + str(self.id)
        logger.debug("MwpsInterface object having name=%s, ofPort=%d and IP=%s was created",
                     self.interfaceName, self.ofPort, self.IP)

class MwsInterface(Interface):

    def __init__(self, intfUuid, interfaceId, ofPort, neObj):
        Interface.__init__(self, intfUuid, interfaceId, ofPort, neObj)
        self.prefixName = 'mws-'
        self.interfaceName = self.prefixName + str(self.id)
        logger.debug("MwsInterface object having name=%s, ofPort=%d and IP=%s was created",
                     self.interfaceName, self.ofPort, self.IP)

class EthInterface(Interface):

    def __init__(self, intfUuid, interfaceId, ofPort, neObj):
        Interface.__init__(self, intfUuid, interfaceId, ofPort, neObj)
        self.prefixName = 'eth-'
        self.interfaceName = self.prefixName + str(self.id)
        logger.debug("EthInterface object having name=%s, ofPort=%d and IP=%s was created",
                     self.interfaceName, self.ofPort, self.IP)
