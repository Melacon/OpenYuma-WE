import logging
import subprocess
import xml.etree.ElementTree as ET
import copy

import wireless_emulator.emulator
from wireless_emulator.utils import addCoreDefaultValuesToNode, printErrorAndExit
import wireless_emulator.interface as Intf

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
        root = self.xmlConfigurationTree.getroot()
        modules = root.findall('module')
        for module in modules:
            if module.get('name') == "microwave-model":
                self.microwaveModuleXmlNode = module
                airInterface = module.find('mw-air-interface-pac')
                self.airInterfacePacXmlNode = copy.deepcopy(airInterface)
                self.microwaveModuleXmlNode.remove(airInterface)
            if module.get('name') == "core-model":
                self.networkElementXmlNode = module.find('network-element')
                ltp = module.find('network-element/ltp')
                self.ltpXmlNode = copy.deepcopy(ltp)
                self.networkElementXmlNode.remove(ltp)

    def buildCoreModelXml(self):
        node = self.networkElementXmlNode
        uuid = node.find('uuid')
        uuid.text = self.uuid
        addCoreDefaultValuesToNode(node,self.uuid)

    def createInterfaces(self):
        ofPort = self.OFPortStart
        portNumId = 1
        for intf in self.interfaces:
            intfObj = None
            if intf['layer'] == "MWPS":

                for port in intf['LTPs']:
                    intfObj = Intf.MwpsInterface(port['id'], portNumId, ofPort, self)
                    ofPort += 1
                    portNumId += 1
                    intfObj.buildXmlFile()
                    self.interfaceList.append(intfObj)

            elif intf['layer'] == "MWS":

                for port in intf['LTPs']:
                    intfObj = Intf.MwsInterface(port['id'], portNumId, ofPort, self)
                    ofPort += 1
                    portNumId += 1
                    intfObj.buildXmlFile()
                    self.interfaceList.append(intfObj)

            elif intf['layer'] == "ETH":

                for port in intf['LTPs']:
                    intfObj = Intf.EthInterface(port['id'], portNumId, ofPort, self)
                    ofPort += 1
                    portNumId += 1
                    intfObj.buildXmlFile()
                    self.interfaceList.append(intfObj)
            else:
                logger.critical("Illegal layer value %s found in JSON configuration file for NE=%s",
                                intf['layer'], self.uuid)
                raise ValueError("Illegal layer value")

    def createDockerContainer(self):
        stringCmd = "docker create -it --privileged -p %s:8300:830 -p %s:2200:22 --name=%s --network=%s yumatest" % \
                    (self.managementIPAddressString, self.managementIPAddressString, self.dockerName, self.networkName)
        cmd = subprocess.Popen(stringCmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        for line in cmd.stderr:
            strLine = line.decode("utf-8").rstrip('\n')
            logger.critical("Stderr: %s", strLine)
            raise RuntimeError

        logger.debug("Created docker container %s having IP=%s", self.dockerName, self.managementIPAddressString)

    def createDockerNetwork(self):
        netAddressString = str(self.networkIPAddress.with_prefixlen)
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

    def startDockerContainer(self):
        stringCmd = "docker start %s" % (self.dockerName)
        cmd = subprocess.Popen(stringCmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        for line in cmd.stderr:
            strLine = line.decode("utf-8").rstrip('\n')
            logger.critical("Stderr: %s", strLine)
            raise RuntimeError

    def addNetworkElement(self):
        self.buildCoreModelXml()
        self.createInterfaces()
        self.createDockerNetwork()
        self.createDockerContainer()
        self.copyXmlConfigFileToDockerContainer()
        self.startDockerContainer()
        #debug purposes
        self.xmlConfigurationTree.write("output" + self.uuid + ".xml")