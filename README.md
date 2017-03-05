# OpenYuma-WE

OpenYuma Wireless Emulator is a wireless transport topology emulation with [OpenYuma](https://github.com/OpenClovis/OpenYuma) NETCONF server, 
based on [ONF TR-532](https://www.opennetworking.org/images/stories/downloads/sdn-resources/technical-reports/TR-532-Microwave-Information-Model-V1.pdf).

### Description

OpenYuma WE takes as input three files:
 * a JSON topology file, with a specific structure, describing the network 
to be emulated.
 * a JSON configuration file giving details about the SDN controller information,
 ranges for the NEs management IP addresses and for the links between the NEs
 * the XML configuration file based on the YANG models 
to be used by each emulated Network Element as a startup configuration and
an XML file containing the status parameters of the model. These two files can 
be automatically generated using a custom version of the [pyang](https://github.com/mbj4668/pyang) utility,
that is available [here](https://github.com/Melacon/pyang-we).

Each NE is emulated as a docker container and exposes a NETCONF server based on the OpenYuma
framework, reflecting an information model based on TR-532 from ONF. All docker containers reside
on top of an [Open vSwitch](http://openvswitch.org/) bridge, and links between different NEs, as 
described in the JSON topology file, are emulated as connections through the OVS bridge. The 
high-level architecture of the emulator is shown below.

![logo](./Architecture.png)

### Prerequisites

These instructions are for Ubuntu.

#### Docker

Install Docker following the instructions from [here](https://store.docker.com/editions/community/docker-ce-server-ubuntu/plans/docker-ce-server-ubuntu-tier?tab=instructions).

Make sure that you follow the instructions also for **Manage Docker as a non-root user** from [here](https://docs.docker.com/engine/installation/linux/linux-postinstall/).

#### Open vSwitch

Install Open VSwitch (I used version 2.6.1 from [here](https://mail.openvswitch.org/pipermail/ovs-announce/2016-November/000093.html)).

After downloading the archive follow the instructions [here](http://docs.openvswitch.org/en/latest/intro/install/general/#build-requirements).


Summary:
```
sudo apt-get install libc-dev libssl-dev python
sudo apt-get install python-pip
pip install six

```

In the location where you extracted the tarball:
```
./configure
make
sudo make install

sudo /sbin/modprobe openvswitch

mkdir -p /usr/local/etc/openvswitch
sudo ovsdb-tool create /usr/local/etc/openvswitch/conf.db \
    vswitchd/vswitch.ovsschema
    
mkdir -p /usr/local/var/run/openvswitch
sudo ovsdb-server --remote=punix:/usr/local/var/run/openvswitch/db.sock \
    --remote=db:Open_vSwitch,Open_vSwitch,manager_options \
    --private-key=db:Open_vSwitch,SSL,private_key \
    --certificate=db:Open_vSwitch,SSL,certificate \
    --bootstrap-ca-cert=db:Open_vSwitch,SSL,ca_cert \
    --pidfile --detach --log-file


sudo ovs-vsctl --no-wait init
```

#### Python 3.6

Install version 3.6 for python:

```
sudo add-apt-repository ppa:jonathonf/python-3.6
sudo apt-get update
sudo apt-get install python3.6
```

#### OpenYuma for WE

Clone the repository from [here](https://github.com/Melacon/OpenYuma).

Build the docker container in there:

```buildoutcfg
docker build -t openyuma .
```

### Install

```
python3.6 setup.py build
sudo python3.6 setup.py install
```

### Usage

The JSON topology configuration file `topology.json` for the topology in the previous figure 
looks like this:

```JSON
{
  "network-elements" : [
    {
      "network-element" :
      {
        "uuid" : "Simulator-1",
        "interfaces" : [
          {
            "layer" : "MWPS",
            "LTPs" : [{"id": "ifIndex1",
              "supportedAlarms" : "signalIsLost, rslIsExceeded, temperatureIsExceeded, modemIsFaulty, radioIsFaulty, modulationIsDownShifted"}]
          },
          {
            "layer" : "MWS",
            "LTPs" : []
          },
          {
            "layer" : "ETH",
            "LTPs" : []
          }
        ]
      }
    },
    {
      "network-element" :
      {
        "uuid" : "Simulator-2",
        "interfaces" : [
          {
            "layer" : "MWPS",
            "LTPs" : [{"id": "ifIndex1",
            "supportedAlarms" : "signalIsLost, rslIsExceeded, temperatureIsExceeded, modemIsFaulty, radioIsFaulty, modulationIsDownShifted"},
              {"id" : "ifIndex2",
              "supportedAlarms" : "signalIsLost, rslIsExceeded, temperatureIsExceeded, modemIsFaulty, radioIsFaulty, modulationIsDownShifted"}]
          },
          {
            "layer" : "MWS",
            "LTPs" : []
          },
          {
            "layer" : "ETH",
            "LTPs" : []
          }
          ]
      }
    },
    {
      "network-element" :
      {
        "uuid" : "Simulator-3",
        "interfaces" : [
          {
            "layer" : "MWPS",
            "LTPs" : [{"id": "ifIndex1",
            "supportedAlarms" : "signalIsLost, rslIsExceeded, temperatureIsExceeded, modemIsFaulty, radioIsFaulty, modulationIsDownShifted"}]
          },
          {
            "layer" : "MWS",
            "LTPs" : []
          },
          {
            "layer" : "ETH",
            "LTPs" : []
          }
          ]
      }
    }
    ],
  "topologies" : {
    "mwps" : {
      "links" : [
        [{"uuid" : "Simulator-1", "ltp" : "ifIndex1", "radio-signal-id" : "26"}, {"uuid" : "Simulator-2", "ltp" : "ifIndex1", "radio-signal-id" : "26"}],
        [{"uuid" : "Simulator-2", "ltp" : "ifIndex2", "radio-signal-id" : "27"}, {"uuid" : "Simulator-3", "ltp" : "ifIndex1", "radio-signal-id" : "27"}]
        ]
    },
    "mws" : {}
  }
}
```

An example emulator configuration file `config.json` is shown below:

```JSON
{
  "controller" :
  {
    "ip-address" : "192.168.254.254",
    "port" : 8181,
    "username" : "admin",
    "password" : "admin"
  },
  "managementIpNetwork" : "192.168.0.0/16",
  "linksIpNetwork" : "10.10.0.0/16",
  "notificationPeriod" : 10
}
```

The information about the SDN controller, where the emulated NEs automatically
register, is available under the `controller` object.

The range for the management IP of the network elements is given by the 
`managementIpNetwork` object, and the range for the IPs of the NE interfaces
is configurable through the `linksIpNetwork` element.

Each  NE is capable of generating a random `problem-notification` NETCONF nofiticaion,
from its available `supported-alarms`. The value of `notificationPeriod` object
represents the amount of seconds between each such  random notifications.

* Starting the emulator is done with the following command (asuming you are in the base folder):

`sudo openyumawe --config=config.json --topo=topology.json --xml=yang/microwave-model-config.xml`

* Stopping the emulator is done with the following command. This will delete 
all the previously created docker containers, docker networks or OVS Bridge or ports

`sudo openyumawe --config=config.json --clean`

### Contact

alex.stancu@radio.pub.ro

alexandrus@ceragon.com