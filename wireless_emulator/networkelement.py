import logging
import subprocess
import xml.etree.ElementTree as ET
import copy
import os

import wireless_emulator.emulator
from wireless_emulator.utils import addCoreDefaultValuesToNode, printErrorAndExit, addCoreDefaultStatusValuesToNode
import wireless_emulator.interface as Intf
from wireless_emulator.odlregistration import registerNeToOdl

logger = logging.getLogger(__name__)

class NetworkElement:

    def __init__(self, neUuid, neId, ofPortStart, interfaces):
        self.uuid = neUuid
        self.id = neId
        self.OFPortStart = ofPortStart
        self.dockerName = self.uuid.replace(" ", "")

        self.emEnv = wireless_emulator.emulator.Emulator()

        self.xmlConfigurationTree = None
        self.networkElementXmlNode = None
        self.ltpXmlNode = None
        self.microwaveModuleXmlNode = None
        self.airInterfacePacXmlNode = None

        self.xmlStatusTree = None
        self.statusXmlNode = None
        self.airInterfaceStatusXmlNode = None
        self.neStatusXmlNode = None
        self.ltpStatusXmlNode = None

        self.networkIPAddress = self.emEnv.mgmtIpFactory.getFreeManagementNetworkIP()
        if self.networkIPAddress is None:
            logger.critical("Could not retrieve a free Management Network IP address for NE=%s", self.uuid)
            raise ValueError("Invalid Network IP address")
        self.managementIPAddressString = str(self.networkIPAddress[1])

        self.interfaces = interfaces

        requiredIntfIpAddresses = 0
        freeIntfIpAddresses = self.emEnv .intfIpFactory.getNumberOfFreeInterfaceIpAddresses()
        for intf in interfaces:
            requiredIntfIpAddresses += len(intf['LTPs'])
        if (requiredIntfIpAddresses > freeIntfIpAddresses):
            logger.critical("Not enough free Interface IP address left for NE=%s", self.uuid)
            raise ValueError("Not enough free Interface IP addresses")

        self.interfaceList = []
        self.networkName = "oywe_net_" + str(self.id)

        tree = ET.parse(self.emEnv.xmlConfigFile)
        if tree is None:
            logger.critical("Could not parse XML default values configuration file!")
            printErrorAndExit()
        else:
            self.xmlConfigurationTree = tree

        tree = ET.parse(self.emEnv.xmlStatusFile)
        if tree is None:
            logger.critical("Could not parse XML default values status file!")
            printErrorAndExit()
        else:
            self.xmlStatusTree = tree

        self.namespaces = {'microwave-model' : 'urn:onf:params:xml:ns:yang:microwave-model',
                           'core-model' : 'urn:onf:params:xml:ns:yang:core-model'}
        self.saveXmlTemplates()

        logger.info("Created NetworkElement object with uuid=%s and id=%s and IP=%s",
                    self.uuid, self.id, self.managementIPAddressString)

    def getNeId(self):
        return self.id

    def getNeUuid(self):
        return self.uuid

    def getInterfaceFromInterfaceUuid(self, reqIntfId):
        for intf in self.interfaceList:
            intfId = intf.getInterfaceUuid()
            if intfId == reqIntfId:
                return intf
        return None

    def saveXmlTemplates(self):
        self.saveConfigXmlTemplates()
        self.saveStatusXmlTemplates()

    def saveConfigXmlTemplates(self):
        config = self.xmlConfigurationTree.getroot()

        self.microwaveModuleXmlNode = config
        airInterface = config.find('microwave-model:mw-air-interface-pac', self.namespaces)
        self.airInterfacePacXmlNode = copy.deepcopy(airInterface)
        self.microwaveModuleXmlNode.remove(airInterface)

        self.networkElementXmlNode = config.find('core-model:network-element', self.namespaces)
        ltp = self.networkElementXmlNode.find('core-model:ltp', self.namespaces)
        self.ltpXmlNode = copy.deepcopy(ltp)
        self.networkElementXmlNode.remove(ltp)

        uselessNode = config.find('microwave-model:co-channel-group', self.namespaces)
        config.remove(uselessNode)

        uselessNode = config.find('microwave-model:mw-air-interface-hsb-end-point-pac', self.namespaces)
        config.remove(uselessNode)

        uselessNode = config.find('microwave-model:mw-air-interface-hsb-fc-switch-pac', self.namespaces)
        config.remove(uselessNode)

        uselessNode = config.find('microwave-model:mw-air-interface-diversity-pac', self.namespaces)
        config.remove(uselessNode)

        uselessNode = config.find('microwave-model:mw-pure-ethernet-structure-pac', self.namespaces)
        config.remove(uselessNode)

        uselessNode = config.find('microwave-model:mw-hybrid-mw-structure-pac', self.namespaces)
        config.remove(uselessNode)

        uselessNode = config.find('microwave-model:mw-ethernet-container-pac', self.namespaces)
        config.remove(uselessNode)

        uselessNode = config.find('microwave-model:mw-tdm-container-pac', self.namespaces)
        config.remove(uselessNode)

        uselessNode = config.find('core-model:forwarding-construct', self.namespaces)
        config.remove(uselessNode)

        uselessNode = config.find('core-model:operation-envelope', self.namespaces)
        config.remove(uselessNode)

        uselessNode = config.find('core-model:equipment', self.namespaces)
        config.remove(uselessNode)

    def saveStatusXmlTemplates(self):
        status = self.xmlStatusTree.getroot()

        self.statusXmlNode = status
        airInterface = status.find('mw-air-interface-pac')
        self.airInterfaceStatusXmlNode = copy.deepcopy(airInterface)
        self.statusXmlNode.remove(airInterface)

        self.neStatusXmlNode = status.find('network-element')
        ltp = self.neStatusXmlNode.find('ltp')
        self.ltpStatusXmlNode = copy.deepcopy(ltp)
        self.neStatusXmlNode.remove(ltp)

        uselessNode = status.find('co-channel-group')
        status.remove(uselessNode)

        uselessNode = status.find('mw-air-interface-hsb-end-point-pac')
        status.remove(uselessNode)

        uselessNode = status.find('mw-air-interface-hsb-fc-switch-pac')
        status.remove(uselessNode)

        uselessNode = status.find('mw-air-interface-diversity-pac')
        status.remove(uselessNode)

        uselessNode = status.find('mw-pure-ethernet-structure-pac')
        status.remove(uselessNode)

        uselessNode = status.find('mw-hybrid-mw-structure-pac')
        status.remove(uselessNode)

        uselessNode = status.find('mw-ethernet-container-pac')
        status.remove(uselessNode)

        uselessNode = status.find('mw-tdm-container-pac')
        status.remove(uselessNode)

        uselessNode = status.find('forwarding-construct')
        status.remove(uselessNode)

        uselessNode = status.find('operation-envelope')
        status.remove(uselessNode)

        uselessNode = status.find('equipment')
        status.remove(uselessNode)

    def buildCoreModelXml(self):
        node = self.networkElementXmlNode
        uuid = node.find('core-model:uuid', self.namespaces)
        uuid.text = self.uuid
        addCoreDefaultValuesToNode(node,self.uuid, self.namespaces, self)

    def buildCoreModelStatusXml(self):
        node = self.neStatusXmlNode
        addCoreDefaultStatusValuesToNode(node)

    def buildNotificationStatusXml(self):
        node = self.statusXmlNode
        notif = ET.SubElement(node, "notifications")
        timeout = ET.SubElement(notif, "timeout")
        timeout.text = str(self.emEnv.configJson['notificationPeriod'])

    def createInterfaces(self):
        ofPort = self.OFPortStart
        portNumId = 1
        for intf in self.interfaces:
            intfObj = None
            if intf['layer'] == "MWPS":

                for port in intf['LTPs']:
                    intfObj = Intf.MwpsInterface(port['id'], portNumId, ofPort, self, port['supportedAlarms'])
                    ofPort += 1
                    portNumId += 1
                    intfObj.buildXmlFiles()
                    self.interfaceList.append(intfObj)

            elif intf['layer'] == "MWS":

                for port in intf['LTPs']:
                    intfObj = Intf.MwsInterface(port['id'], portNumId, ofPort, self, port['supportedAlarms'])
                    ofPort += 1
                    portNumId += 1
                    intfObj.buildXmlFiles()
                    self.interfaceList.append(intfObj)

            elif intf['layer'] == "ETH":

                for port in intf['LTPs']:
                    intfObj = Intf.EthInterface(port['id'], portNumId, ofPort, self, port['supportedAlarms'])
                    ofPort += 1
                    portNumId += 1
                    intfObj.buildXmlFiles()
                    self.interfaceList.append(intfObj)
            else:
                logger.critical("Illegal layer value %s found in JSON configuration file for NE=%s",
                                intf['layer'], self.uuid)
                raise ValueError("Illegal layer value")

    def createDockerContainer(self):
        print("Creating docker container %s..." % (self.dockerName))

        stringCmd = "docker create -it --privileged -p %s:8300:830 -p %s:2200:22 --name=%s --network=%s openyuma" % \
                    (self.managementIPAddressString, self.managementIPAddressString, self.dockerName, self.networkName)
        cmd = subprocess.Popen(stringCmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        for line in cmd.stderr:
            strLine = line.decode("utf-8").rstrip('\n')
            logger.critical("Stderr: %s", strLine)
            raise RuntimeError

        logger.debug("Created docker container %s having IP=%s", self.dockerName, self.managementIPAddressString)

    def createDockerNetwork(self):

        netAddressString = str(self.networkIPAddress.with_prefixlen)
        print("Creating docker network %s..." % (netAddressString))

        stringCmd = "docker network create -d bridge --subnet=%s --ip-range=%s %s" % \
                    (netAddressString, netAddressString, self.networkName)
        cmd = subprocess.Popen(stringCmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        for line in cmd.stderr:
            strLine = line.decode("utf-8").rstrip('\n')
            logger.critical("Stderr: %s", strLine)
            raise RuntimeError

        logger.debug("Created docker network %s having address %s", self.networkName, netAddressString)

    def copyXmlConfigFileToDockerContainer(self):
        outFileName = "startup-cfg.xml"
        self.xmlConfigurationTree.write(outFileName)
        targetPath = "/usr/src/OpenYuma"

        stringCmd = "docker cp %s %s:%s" % \
                    (outFileName, self.dockerName, targetPath)
        cmd = subprocess.Popen(stringCmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        for line in cmd.stderr:
            strLine = line.decode("utf-8").rstrip('\n')
            logger.critical("Stderr: %s", strLine)
            raise RuntimeError

        stringCmd = "rm -f %s" % (outFileName)
        cmd = subprocess.Popen(stringCmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        for line in cmd.stderr:
            strLine = line.decode("utf-8").rstrip('\n')
            logger.critical("Stderr: %s", strLine)
            raise RuntimeError

    def copyXmlStatusFileToDockerContainer(self):
        outFileName = "microwave-model-status.xml"
        self.xmlStatusTree.write(outFileName)
        targetPath = "/usr/src/OpenYuma"

        stringCmd = "docker cp %s %s:%s" % \
                    (outFileName, self.dockerName, targetPath)
        cmd = subprocess.Popen(stringCmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        for line in cmd.stderr:
            strLine = line.decode("utf-8").rstrip('\n')
            logger.critical("Stderr: %s", strLine)
            raise RuntimeError

        stringCmd = "rm -f %s" % (outFileName)
        cmd = subprocess.Popen(stringCmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        for line in cmd.stderr:
            strLine = line.decode("utf-8").rstrip('\n')
            logger.critical("Stderr: %s", strLine)
            raise RuntimeError

    def startDockerContainer(self):
        stringCmd = "docker start %s" % (self.dockerName)
        cmd = subprocess.Popen(stringCmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        for line in cmd.stderr:
            strLine = line.decode("utf-8").rstrip('\n')
            logger.critical("Stderr: %s", strLine)
            raise RuntimeError

    def copyYangFilesToDockerContainer(self):

        directory = 'yang'
        for filename in os.listdir(directory):
            if filename.endswith(".yang"):
                stringCmd = "docker cp %s %s:%s" % \
                            (os.path.join(directory, filename), self.dockerName, "/usr/share/yuma/modules")
                cmd = subprocess.Popen(stringCmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                for line in cmd.stderr:
                    strLine = line.decode("utf-8").rstrip('\n')
                    logger.critical("Stderr: %s", strLine)
                    raise RuntimeError



    def addNetworkElement(self):
        print("Adding Network element %s..." % (self.uuid))
        self.buildCoreModelXml()
        self.buildCoreModelStatusXml()
        self.buildNotificationStatusXml()

        self.createInterfaces()

        self.createDockerNetwork()
        self.createDockerContainer()

        self.copyXmlConfigFileToDockerContainer()
        self.copyXmlStatusFileToDockerContainer()
        self.copyYangFilesToDockerContainer()

        self.startDockerContainer()
        if self.emEnv.registerToOdl == True:
            try:
                registerNeToOdl(self.emEnv.controllerInfo, self.uuid, self.managementIPAddressString)
            except RuntimeError:
                print("Failed to register NE=%s having IP=%s to the ODL controller" % (self.uuid, self.managementIPAddressString))

        #debug
        self.xmlConfigurationTree.write('output-config-' + self.dockerName + '.xml')
        self.xmlStatusTree.write('output-status-' + self.dockerName + '.xml')

