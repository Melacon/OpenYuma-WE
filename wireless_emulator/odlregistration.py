import requests, json
import xml.etree.ElementTree as ET

import logging

logger = logging.getLogger(__name__)

def registerNeToOdl(controllerInfo, neUuid, neManagementIp):

    print("Registering NE=%s having IP=%s to ODL controller" % (neUuid, neManagementIp))

    xmlTree = createXmlPayloadForOdl(neUuid, neManagementIp)

    root = xmlTree.getroot()

    url = 'http://{}:{}/restconf/config/network-topology:network-topology/topology/topology-netconf/node/controller-config/yang-ext:mount/config:modules'.format(
        controllerInfo['ip-address'], controllerInfo['port'])
    headers = {
        'content-type': "application/xml",
        'cache-control': "no-cache"
    }

    payload = ET.tostring(root)

    #debug
    xmlTree.write("odlRegistration.xml")

    response = requests.request("POST", url, data=payload, headers=headers, auth=(controllerInfo['username'], controllerInfo['password']))

    if response.status_code == 204:
        print("Successfully registered NE=%s to ODL controller" % neUuid)
        logger.info("Successfully registered NE=%s to ODL controller", neUuid)
    else:
        logger.error("Could not register NE=%s to ODL controller", neUuid)
        logger.error(json.dumps(json.loads(response.text), indent=4))
        raise RuntimeError

def unregisterNeFromOdl(controllerInfo, neUuid):

    print("Unregistering NE=%s from ODL controller" % neUuid)

    url = "http://{}:{}/restconf/config/network-topology:network-topology/topology/topology-netconf/node/" \
          "controller-config/yang-ext:mount/config:modules/module/odl-sal-netconf-connector-cfg:sal-netconf-connector/" \
          "{}".format(controllerInfo['ip-address'], controllerInfo['port'], neUuid)
    headers = {
        'content-type': "application/xml",
        'cache-control': "no-cache"
    }
    response = requests.request("DELETE", url, headers=headers, auth=('admin', 'admin'))

    if response.status_code == 200:
        print("Successfully unregistered NE=%s from ODL controller" % neUuid)
        logger.info("Successfully unregistered NE=%s from ODL controller", neUuid)
    else:
        logger.error("Could not unregister NE=%s from ODL controller", neUuid)
        logger.error(json.dumps(json.loads(response.text), indent=4))
        raise RuntimeError

def createXmlPayloadForOdl(neUuid, neManagementIp):
    netconfNs = "urn:opendaylight:params:xml:ns:yang:controller:md:sal:connector:netconf"

    module = ET.Element("module", xmlns="urn:opendaylight:params:xml:ns:yang:controller:config")

    type = ET.SubElement(module, "type")
    type.text = "prefix:sal-netconf-connector"
    type.set('xmlns:prefix', netconfNs)

    ET.SubElement(module, "name").text = neUuid
    address = ET.SubElement(module, "address")
    address.text = neManagementIp
    address.set('xmlns', netconfNs)

    port = ET.SubElement(module, "port")
    port.text = "8300"
    port.set('xmlns', netconfNs)

    username = ET.SubElement(module, "username")
    username.text = "admin"
    username.set('xmlns', netconfNs)

    password = ET.SubElement(module, "password")
    password.text = "admin"
    password.set('xmlns', netconfNs)

    tcponly = ET.SubElement(module, "tcp-only")
    tcponly.text = "false"
    tcponly.set('xmlns', netconfNs)

    eventExecutor = ET.SubElement(module, "event-executor")
    eventExecutor.set('xmlns', netconfNs)

    etype = ET.SubElement(eventExecutor, "type")
    etype.text = "prefix:netty-event-executor"
    etype.set('xmlns:prefix', "urn:opendaylight:params:xml:ns:yang:controller:netty")
    ET.SubElement(eventExecutor, "name").text = "global-event-executor"

    bindingRegistry = ET.SubElement(module, "binding-registry")
    bindingRegistry.set('xmlns', netconfNs)

    btype = ET.SubElement(bindingRegistry, "type")
    btype.text = "prefix:binding-broker-osgi-registry"
    btype.set('xmlns:prefix', "urn:opendaylight:params:xml:ns:yang:controller:md:sal:binding")
    ET.SubElement(bindingRegistry, "name").text = "binding-osgi-broker"

    domRegistry = ET.SubElement(module, "dom-registry")
    domRegistry.set('xmlns', netconfNs)

    dtype = ET.SubElement(domRegistry, "type")
    dtype.text = "prefix:dom-broker-osgi-registry"
    dtype.set('xmlns:prefix', "urn:opendaylight:params:xml:ns:yang:controller:md:sal:dom")
    ET.SubElement(domRegistry, "name").text = "dom-broker"

    clientDispatcher = ET.SubElement(module, "client-dispatcher")
    clientDispatcher.set('xmlns', netconfNs)

    ctype = ET.SubElement(clientDispatcher, "type")
    ctype.text = "prefix:netconf-client-dispatcher"
    ctype.set('xmlns:prefix', "urn:opendaylight:params:xml:ns:yang:controller:config:netconf")
    ET.SubElement(clientDispatcher, "name").text = "global-netconf-dispatcher"

    processingExecutor = ET.SubElement(module, "processing-executor")
    processingExecutor.set('xmlns', netconfNs)

    ptype = ET.SubElement(processingExecutor, "type")
    ptype.text = "prefix:threadpool"
    ptype.set('xmlns:prefix', "urn:opendaylight:params:xml:ns:yang:controller:threadpool")
    ET.SubElement(processingExecutor, "name").text = "global-netconf-processing-executor"

    keepaliveExecutor = ET.SubElement(module, "keepalive-executor")
    keepaliveExecutor.set('xmlns', netconfNs)

    ktype = ET.SubElement(keepaliveExecutor, "type")
    ktype.text = "prefix:scheduled-threadpool"
    ktype.set('xmlns:prefix', "urn:opendaylight:params:xml:ns:yang:controller:threadpool")
    ET.SubElement(keepaliveExecutor, "name").text = "global-netconf-ssh-scheduled-executor"

    return ET.ElementTree(module)
