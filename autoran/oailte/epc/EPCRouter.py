from ipaddress import IPv4Interface, IPv4Network, IPv4Address
from threading import Thread, Lock
import docker
import time
import re
from loguru import logger
from dataclasses_json import config, dataclass_json
from dataclasses import dataclass, field
import time

from autoran.utils.command_runner import RemoteRunner, terminate_container

class CoreRouter():
    def __init__(self,
        client: docker.APIClient,
        ue_network: str,
        spgwu_public_ip: str,
        public_bridge_ip: str,
        remote_runner: RemoteRunner,
        routing_config: dict,
    ):
        # thread-safe
        self.mutex = Lock()

        self.client = client
        self.ue_network = ue_network
        self.spgwu_public_ip = spgwu_public_ip
        self.public_bridge_ip = public_bridge_ip
        self.rr = remote_runner
        self.routing_config = routing_config
        self.successful_commands = []

        # expose UE ips assigned by LTE through spgw-u
        self.rr.run_command("ip route add {0} via {1} ".format(self.ue_network,self.spgwu_public_ip))
        logger.info('EPC router at {0} exposed UE LTE ips {1} through spgw-u {2}.'.format(self.client.base_url,self.ue_network,self.spgwu_public_ip))
        self.successful_commands.append('init_routing')

        self.tunnel_counter = 0

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


    def enable_iptables_forwarding(self, 
        tunnel_name: str,
    ):

        # this command only works for 1 ue connection

        self.mutex.acquire()

        # do not run a command multiple times
        if "iptables" in self.successful_commands:
            return

        command_str = "iptables-save > /tmp/dsl.fw"
        if self.iptables_command(command_str):
            logger.info('Iptables at EPC {0} is saved to {1}.'.format(self.client.base_url,'/tmp/dsl.fw'))
        else:
            return


        ext_if = self.routing_config['epc_ex_net_if']
        tun_if = tunnel_name

        command = ("iptables -t nat -A POSTROUTING -o {0} -j MASQUERADE && ".format(ext_if)
                + "iptables -A FORWARD -i {0} -o {1} -m state --state RELATED,ESTABLISHED -j ACCEPT && ".format(ext_if,tun_if)
                + "iptables -A FORWARD -i {0} -o {1} -j ACCEPT && ".format(tun_if,ext_if)
                + "iptables -t nat -A POSTROUTING -o {0} -j MASQUERADE && ".format(tun_if)
                + "iptables -A FORWARD -i {0} -o {1} -m state --state RELATED,ESTABLISHED -j ACCEPT && ".format(tun_if,ext_if)
                + "iptables -A FORWARD -i {0} -o {1} -j ACCEPT".format(ext_if,tun_if) )

        #print(command)

        self.rr.run_command(command)
        logger.info('EPC router at {0} enabled ip MASQUERADE between interfaces {1} and {2}.'.format(self.client.base_url,tun_if,ext_if))
        self.successful_commands.append("iptables")

        self.mutex.release()


    def restore_iptables(self):
        self.mutex.acquire()

        ext_if = self.routing_config['epc_ex_net_if']

        if "iptables" in self.successful_commands:

            command_str = "iptables-restore < /tmp/dsl.fw"
            self.iptables_command(command_str)

            self.successful_commands.remove("iptables")
            logger.warning('EPC router at {0} restored iptables.'.format(self.client.base_url))

        self.mutex.release()


    def wait_for_tunnel(self,
        tunnel_ue_ip: str,
    ):
        return self.rr.run_command(command="ping -c7 {0}".format(tunnel_ue_ip),timeout=10)

    def create_tunnel_route(self,
        tunnel_name: str,
        target_net: str,
        ue_tunnel_ip: str,
    ):
        self.mutex.acquire()

        # expose external UE ips through the tunnel
        self.rr.run_command("ip route add {0} via {1} dev {2} ".format(target_net,ue_tunnel_ip,tunnel_name))
        logger.info('EPC router at {0} exposed external UE network {1} through tunnel {2}.'.format(self.client.base_url,target_net,tunnel_name))
        self.successful_commands.append(target_net)

        self.mutex.release()

    def remove_tunnel_route(self,
        target_net: str,
    ):
        self.mutex.acquire()

        if target_net in self.successful_commands:
            self.rr.run_command("ip route del {0}".format(target_net))
            self.successful_commands.remove(target_net)
            logger.warning('EPC router at {0} deleted UE ext network route {1}'.format(self.client.base_url,target_net))

        self.mutex.release()

    def create_tunnel(self,
        remote_ip: str,
        local_ip: str,
        tunnel_epc_if: str,
    ):
        self.mutex.acquire()

        # create tunnel name
        name = 'tun'+str(self.tunnel_counter)

        self.rr.run_command("ip tunnel add {0} mode gre remote {1} local {2} ".format(name,remote_ip,local_ip))
        self.rr.run_command("ip addr add {0} dev {1}".format(tunnel_epc_if,name))
        self.rr.run_command("ip link set {0} up".format(name))
        logger.info('EPC router at {0} created tunnel {1} between {2} and {3} with tunnel interface: {4}'.format(self.client.base_url,name,local_ip,remote_ip,tunnel_epc_if))
        self.successful_commands.append(name)

        # increase tunnel counter
        self.tunnel_counter=self.tunnel_counter+1

        self.mutex.release()

        return name

    def remove_tunnel(self,
        name: str,
    ):
        self.mutex.acquire()

        if name in self.successful_commands:
            self.rr.run_command("ip tunnel del {0}".format(name))
            self.successful_commands.remove(name)
            logger.warning('EPC router at {0} deleted tunnel {1}'.format(self.client.base_url,name))

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
        for command in self.successful_commands:
            if 'tun' in command:
                self.remove_tunnel(command)

        # clean first route command
        if 'init_routing' in self.successful_commands:
            self.rr.run_command("ip route del {0} ".format(self.ue_network))
            self.successful_commands.remove('init_routing')
            logger.warning('EPC router at {0} deleted route to UE LTE ips {1}.'.format(self.client.base_url,self.ue_network))



