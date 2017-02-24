import logging
import subprocess

logger = logging.getLogger(__name__)

def cleanup():
    dockerNames = getDockerNames()
    dockerNetworks = getDockerNetworks()

    stopAndRemoveDockerContainers(dockerNames)
    removeDockerNetworks(dockerNetworks)

    print("All cleaned up!")
    return True

def getDockerNames():
    dockerNamesList = []

    stringCmd = "docker ps -a | grep yumatest | awk '{print $12}'"

    cmd = subprocess.Popen(stringCmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    for line in cmd.stderr:
        strLine = line.decode("utf-8").rstrip('\n')
        logger.critical("Could not get names of docker containers having image yumatest.\n Stderr: %s", strLine)
        raise RuntimeError("Could not get docker container names")

    for line in cmd.stdout:
        strLine = line.decode("utf-8").rstrip('\n')
        dockerNamesList.append(strLine)

    return dockerNamesList


def getDockerNetworks():
    dockerNetworksList = []

    stringCmd = "docker network ls | grep oywe | awk '{print $2}'"

    cmd = subprocess.Popen(stringCmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    for line in cmd.stderr:
        strLine = line.decode("utf-8").rstrip('\n')
        logger.critical("Could not get names of docker networks having names oywe.\n Stderr: %s", strLine)
        raise RuntimeError("Could not get docker networks")

    for line in cmd.stdout:
        strLine = line.decode("utf-8").rstrip('\n')
        dockerNetworksList.append(strLine)

    return dockerNetworksList

def stopAndRemoveDockerContainers(dockerNames):
    for container in dockerNames:
        print("Stopping docker container %s" % container)
        stringCmd = "docker stop %s" % (container)

        cmd = subprocess.Popen(stringCmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        for line in cmd.stderr:
            strLine = line.decode("utf-8").rstrip('\n')
            logger.critical("Could not stop docker container %s\n Stderr: %s", container, strLine)
            raise RuntimeError("Could not stop docker container %s" % container)

        print("Removing docker container %s" % container)
        stringCmd = "docker rm %s" % (container)

        cmd = subprocess.Popen(stringCmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        for line in cmd.stderr:
            strLine = line.decode("utf-8").rstrip('\n')
            logger.critical("Could not remove docker container %s\n Stderr: %s", container, strLine)
            raise RuntimeError("Could not remove docker container ")

def removeDockerNetworks(dockerNetworks):
    for network in dockerNetworks:
        print("Removing docker network %s" % network)
        stringCmd = "docker network rm %s" % (network)

        cmd = subprocess.Popen(stringCmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        for line in cmd.stderr:
            strLine = line.decode("utf-8").rstrip('\n')
            logger.critical("Could not remove docker network %s\n Stderr: %s" % network, strLine)
            raise RuntimeError("Could not remove docker container %s" % network)
