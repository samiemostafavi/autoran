from ipaddress import IPv4Interface, IPv4Network, IPv4Address
import docker
from loguru import logger
from dataclasses_json import config, dataclass_json
from dataclasses import dataclass, field


class DockerNetwork():
    def __init__(self,
                client: docker.APIClient,
                network: IPv4Network,
                name: str):
        """
        Parameters
        ----------
        client
            Docker API client
        network
            Network subnet
        name
            Name of the network
        """
        logger.info('Setting up docker network {0} {1}'.format(name,str(network)))

        # check if there is a network with this name
        found_nets = client.networks(names=[name])
        if len(found_nets) == 0:
            logger.info('Did not find network {0} in docker, hence creating it.'.format(name))
            ipam_pool = docker.types.IPAMPool(
                subnet=str(network),
            )
            ipam_config = docker.types.IPAMConfig(
                pool_configs=[ipam_pool]
            )
            self.docker_network_dict = client.create_network(name,ipam=ipam_config)
            self.network = network
            self.name = name
            self.client = client
        else:
            logger.info('Network {0} was found in docker.'.format(name))
            self.docker_network_dict = found_nets[0]
            self.network = network
            self.client = client
            self.name = name


    def __del__(self):

        logger.warning("Removing docker network {0} {1}.".format(self.name,str(self.network)))
        try:
            self.client.remove_network(self.docker_network_dict['Id'])
        except Exception as e:
            logger.error(str(e))



# EPC Docker Service Abstract
@dataclass_json
@dataclass(frozen=False, eq=True)
class DockerService:
    name: str
    client: docker.APIClient
    container: dict

    def __del__(self):

        logger.warning("Tearing down service {0} at {1}.".format(self.name,self.client.base_url))
        try:
            self.client.kill(self.container)
        except Exception as e:
            logger.error(str(e))

        try:
            self.client.remove_container(self.container)
        except Exception as e:
            logger.error(str(e))
