from ipaddress import IPv4Interface, IPv4Network, IPv4Address
import docker
from loguru import logger
from dataclasses_json import config, dataclass_json
from dataclasses import dataclass, field


class DockerNetwork():
    def __init__(self,
                host: str,
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
        # connect to the EPC host dockerhub
        self.host_name = host
        self.name = name
        self.docker_port = '2375'
        self.client = docker.APIClient(base_url=self.host_name+':'+self.docker_port)

        logger.info('Setting up docker network {0} {1} at {2}'.format(name,str(network),self.host_name))

        # check if there is a network with this name
        found_nets = self.client.networks(names=[name])
        if len(found_nets) == 0:
            logger.info('Did not find network {0} in docker, hence creating it.'.format(name))
            ipam_pool = docker.types.IPAMPool(
                subnet=str(network),
            )
            ipam_config = docker.types.IPAMConfig(
                pool_configs=[ipam_pool]
            )
            self.docker_network_dict = self.client.create_network(name,ipam=ipam_config)
            self.network = network
        else:
            logger.info('Network {0} was found in docker.'.format(name))
            self.docker_network_dict = found_nets[0]
            self.network = network
            # TODO 
            # FIND THE ALLOCATED ADDRESSES AND ADD THEM TO THE self.network_reserved
        
        hosts_iterator = (host for host in self.network.hosts())
        self.docker_bridge_ip = str(next(hosts_iterator))
        self.network_reserved = {self.docker_bridge_ip} # the first address is the docker bridge ip


    def allocate_ip(self):
        hosts_iterator = (host for host in self.network.hosts() if str(host) not in self.network_reserved)
        ip = str(next(hosts_iterator))
        self.network_reserved.add(ip)
        return ip

    def deallocate_ip(self,
            ip: str,
            ):
        if ip in self.network_reserved:
            self.network_reserved.remove(ip)


    def __del__(self):

        logger.warning("Removing docker network {0} {1} at {2}.".format(self.name,str(self.network),self.host_name))
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
