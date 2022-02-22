from ipaddress import IPv4Interface, IPv4Network, IPv4Address
import docker
import time
import re
from loguru import logger
from dataclasses_json import config, dataclass_json
from dataclasses import dataclass, field
import time

from lib.utils.router_admin import run_command 

class CoreRouter():
    def __init__(self,
        client: docker.APIClient,
        ue_network: str,
        spgwu_public_ip: str,
        public_bridge_ip: str,
    ):

        self.client = client
        self.ue_network = ue_network
        self.spgwu_public_ip = spgwu_public_ip
        self.public_bridge_ip = public_bridge_ip
        self.successful_commands = []

        # expose UE ips assigned by LTE through spgw-u
        run_command(self.client,"ip route add {0} via {1} ".format(self.ue_network,self.spgwu_public_ip))
        logger.info('EPC Router at {0} exposed UE LTE ips {1} through spgw-u {2}.'.format(self.client.base_url,self.ue_network,self.spgwu_public_ip))
        self.successful_commands.append('init_routing')

        

    def __del__(self):

        # clean first route command
        if 'init_routing' in self.successful_commands:
            run_command(self.client,"ip route del {0} ".format(self.ue_network))
            self.successful_commands.remove('init_routing')
            logger.warning('EPC Router at {0} deleted route to UE LTE ips {1}.'.format(self.client.base_url,self.ue_network))



