from ipaddress import IPv4Interface, IPv4Network, IPv4Address
from threading import Thread, Lock
import docker
import time
import re
from loguru import logger
from dataclasses_json import config, dataclass_json
from dataclasses import dataclass, field
import time

from lib.utils.command_runner import RemoteRunner, terminate_container

class UERouter():
    def __init__(self,
        client: docker.APIClient,
        docker_public_network: str,
        epc_main_lte_ip: str,
        epc_bridge_ip: str,
        lte_assigned_ip: str,
        remote_runner: RemoteRunner,
        routing_config: dict,
    ):
        # thread-safe
        self.mutex = Lock()

        self.client = client
        self.routing_config = routing_config
        self.docker_public_network = docker_public_network
        self.epc_main_lte_ip = epc_main_lte_ip
        self.epc_bridge_ip = epc_bridge_ip
        self.lte_assigned_ip = lte_assigned_ip
        self.rr = remote_runner

        self.successful_commands = []

        # expose EPC Host docker bridge interface
        self.rr.run_command("ip route add {0} via {1} dev oaitun_ue1".format(self.docker_public_network,self.epc_main_lte_ip))
        logger.info('UE Router at {0} exposed EPC docker public network {1} through LTE main ip {2}.'.format(self.client.base_url,self.docker_public_network,self.epc_main_lte_ip))
        self.successful_commands.append('init_routing')

        self.create_tunnel(
            remote_ip=self.epc_bridge_ip,
            local_ip=self.lte_assigned_ip,
            tunnel_ue_if=str(routing_config['ue_tun_if']),
        )

    def iptables_command(self,command_str):


        container = self.client.create_container(
            image='router_admin:latest',
            name='iptables_saver',
            hostname='ubuntu',
            volumes=['/tmp/'],
            host_config=self.client.create_host_config(
                network_mode='host',
                privileged=True,
                binds=[
                    '/tmp/:/tmp/',
                ],
            ),
            command="/bin/bash -c  \" " + command_str + " && echo 'OK' \" "
        )

        # start the container
        self.client.start(container)

        success = False
        for i in range(1,10):
            time.sleep(0.1)
            logs = self.client.logs(container,stdout=True, stderr=True, tail='all')
            logs = logs.decode().rstrip()
            #print(logs)
            if "OK" in logs:
                success = True
                break
        if not success:
            logger.error('Running the command: \" ' + command_str + " \" did not work on {0}".format(self.client.base_url))
            terminate_container(self.client,container)
            return False
            #raise Exception('Running the routing command: \" ' + command + " \" did not work on {0}".format(client.base_url))

        terminate_container(self.client,container)
        return True


    def enable_iptables_forwarding(self):

        self.mutex.acquire()

        # do not run a command multiple times
        if "iptables" in self.successful_commands:
            return

        command_str = "iptables-save > /tmp/dsl.fw"
        if self.iptables_command(command_str):
            logger.info('Iptables at UE {0} is saved to {1}.'.format(self.client.base_url,'/tmp/dsl.fw'))
        else:
            return

        
        ext_if = self.routing_config['ue_ex_net_if']
        tun_if = 'tun0'

        command = ("iptables -t nat -A POSTROUTING -o {0} -j MASQUERADE && ".format(ext_if)
                + "iptables -A FORWARD -i {0} -o {1} -m state --state RELATED,ESTABLISHED -j ACCEPT && ".format(ext_if,tun_if)
                + "iptables -A FORWARD -i {0} -o {1} -j ACCEPT && ".format(tun_if,ext_if)
                + "iptables -t nat -A POSTROUTING -o {0} -j MASQUERADE && ".format(tun_if)
                + "iptables -A FORWARD -i {0} -o {1} -m state --state RELATED,ESTABLISHED -j ACCEPT && ".format(tun_if,ext_if)
                + "iptables -A FORWARD -i {0} -o {1} -j ACCEPT".format(ext_if,tun_if) )

        #print(command)

        self.rr.run_command(command)
        logger.info('UE router at {0} enabled ip MASQUERADE between interfaces {1} and {2}.'.format(self.client.base_url,tun_if,ext_if))
        self.successful_commands.append("iptables")

        self.mutex.release()

    def restore_iptables(self):
        self.mutex.acquire()

        ext_if = self.routing_config['ue_ex_net_if']
        tun_if = 'tun0'

        if "iptables" in self.successful_commands:
            
            command_str = "iptables-restore < /tmp/dsl.fw"
            self.iptables_command(command_str)

            self.successful_commands.remove("iptables")
            logger.warning('UE router at {0} deleted MASQUERADE between interfaces {1} and {2}.'.format(self.client.base_url,tun_if,ext_if))

        self.mutex.release()


    def create_tunnel_route(self,
        target_net: str,
        epc_tunnel_ip: str,
    ):
        self.mutex.acquire()
        
        tunnel_name = 'tun0'

        # expose external UE ips through the tunnel
        self.rr.run_command("ip route add {0} via {1} dev {2} ".format(target_net,epc_tunnel_ip,tunnel_name))
        logger.info('UE router at {0} exposed external EPC network {1} through tunnel {2}.'.format(self.client.base_url,target_net,tunnel_name))
        self.successful_commands.append(target_net)

        self.mutex.release()

    def remove_tunnel_route(self,
        target_net: str,
    ):
        self.mutex.acquire()

        if target_net in self.successful_commands:
            self.rr.run_command("ip route del {0}".format(target_net))
            self.successful_commands.remove(target_net)
            logger.warning('UE router at {0} deleted EPC ext network route {1}'.format(self.client.base_url,target_net))

        self.mutex.release()


    def wait_for_tunnel(self,
        tunnel_epc_ip: str,
    ):
        return self.rr.run_command(command="ping -c7 {0}".format(tunnel_epc_ip),timeout=10)

    def create_tunnel(self,
        remote_ip: str,
        local_ip: str,
        tunnel_ue_if: str,
    ):
        self.mutex.acquire()

        # create tunnel name
        name = 'tun0'

        self.rr.run_command("ip tunnel add {0} mode gre remote {1} local {2} ".format(name,remote_ip,local_ip))
        self.rr.run_command("ip addr add {0} dev {1}".format(tunnel_ue_if,name))
        self.rr.run_command("ip link set {0} up".format(name))
        logger.info('UE router at {0} created tunnel {1} between {2} and {3} with tunnel interface: {4}'.format(self.client.base_url,name,local_ip,remote_ip,tunnel_ue_if))
        self.successful_commands.append(name)

        self.mutex.release()

        return name

    def remove_tunnel(self,
        name: str,
    ):
        self.mutex.acquire()

        if name in self.successful_commands:
            self.rr.run_command("ip tunnel del {0}".format(name))
            self.successful_commands.remove(name)
            logger.warning('UE router at {0} deleted tunnel {1}'.format(self.client.base_url,name))

        self.mutex.release()

    def __del__(self):

        # clean the iptables
        if "iptables" in self.successful_commands:
            self.restore_iptables()

        # clean the ext_routes
        for command in self.successful_commands:
            if '/' in command:
                self.remove_tunnel_route(command)

        # clean the tunnels
        if 'tun0' in self.successful_commands:
            self.remove_tunnel('tun0')

        # clean first route command
        if 'init_routing' in self.successful_commands:
            self.rr.run_command("ip route del {0} ".format(self.docker_public_network))
            self.successful_commands.remove('init_routing')
            logger.warning('UE Router at {0} deleted route to EPC docker public network {1}.'.format(self.client.base_url,self.docker_public_network))



