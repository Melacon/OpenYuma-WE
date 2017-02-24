import json
import logging
import subprocess
import xml.etree.ElementTree as ET
import copy

from wireless_emulator.utils import printErrorAndExit
from wireless_emulator.ip import ManagementNetworkIPFactory, InterfaceIPFactory, MacAddressFactory
import wireless_emulator.networkelement as NE
from wireless_emulator.utils import Singleton
from wireless_emulator.topology import Topology

logger = logging.getLogger(__name__)

class Emulator(metaclass=Singleton):

    def __init__(self, topologyFileName = None, xmlConfigFile = None):
        self.networkElementList = []
        self.topologies = []
        self.controllerInfo = {}
        self.mgmtIpFactory = ManagementNetworkIPFactory()
        self.intfIpFactory = InterfaceIPFactory()
        self.macAddressFactory = MacAddressFactory()
        self.topoJson = None
        self.xmlConfigFile = xmlConfigFile


        try:
            with open(topologyFileName) as json_data:
                self.topoJson = json.load(json_data)
        except IOError as err:
            logger.critical("Could not open topology file=%s", topologyFileName)
            logger.critical("I/O error({0}): {1}".format(err.errno, err.strerror))
            printErrorAndExit()

        self.createMainBridge()

    def createMainBridge(self):
        cmd = subprocess.Popen('ovs-vsctl list-br', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        for line in cmd.stdout:
            bridge = line.decode("utf-8").rstrip('\n')
            if bridge == "oywe-br":
                cmd = subprocess.Popen('ovs-vsctl del-br oywe-br', shell=True, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
                logger.info("Bridge %s already present, deleting it", bridge)
                break

        cmd = subprocess.Popen('ovs-vsctl add-br oywe-br',
                               shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logger.info("Bridge oywe-br created!")

    def createNetworkElements(self):
        logger.debug("Creating Network Elements")

        neId = 1
        ofPortStart = 1
        for ne in self.topoJson['network-elements']:
            neUuid = ne['network-element']['uuid']
            interfaces = ne['network-element']['interfaces']
            neObj = None
            try:
                neObj = NE.NetworkElement(neUuid, neId, ofPortStart, interfaces)
            except ValueError:
                logger.critical("Could not create Network Element=%s", neUuid)
                printErrorAndExit()
            neObj.addNetworkElement()
            self.networkElementList.append(neObj)
            neId += 1

    def createTopologiesList(self):

        logger.debug("Creating topologies list...")

        mwpsTopo = self.topoJson['topologies']['mwps']

        topoObj = Topology(mwpsTopo, "mwps")
        self.topologies.append(topoObj)

    def buildTopologies(self):
        logger.debug("Building topologies...")
        for topo in self.topologies:
            topo.buildTopology()

    def createTopologies(self):
        self.createTopologiesList()
        self.buildTopologies()