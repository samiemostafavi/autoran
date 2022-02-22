from ipaddress import IPv4Interface, IPv4Network, IPv4Address
import docker
import time
import re
from loguru import logger
from dataclasses_json import config, dataclass_json
from dataclasses import dataclass, field
import time

from lib.utils.router_admin import run_command 

class UERouter():
    def __init__(self,
        client: docker.APIClient,
        docker_public_network: str,
        epc_main_lte_ip: str,
        epc_bridge_ip: str,
    ):

        self.client = client
        self.docker_public_network = docker_public_network
        self.epc_main_lte_ip = epc_main_lte_ip
        self.epc_bridge_ip = epc_bridge_ip
        self.successful_commands = []

        # expose EPC Host docker bridge interface
        run_command(self.client,"ip route add {0} via {1} dev oaitun_ue1".format(self.docker_public_network,self.epc_main_lte_ip))
        logger.info('UE Router at {0} exposed EPC docker public network {1} through LTE main ip {2}.'.format(self.client.base_url,self.docker_public_network,self.epc_main_lte_ip))
        self.successful_commands.append('init_routing')

        

    def __del__(self):

        # clean first route command
        if 'init_routing' in self.successful_commands:
            run_command(self.client,"ip route del {0} ".format(self.docker_public_network))
            self.successful_commands.remove('init_routing')
            logger.warning('UE Router at {0} deleted route to EPC docker public network {1}.'.format(self.client.base_url,self.docker_public_network))



