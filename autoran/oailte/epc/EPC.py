from ipaddress import IPv4Interface, IPv4Network, IPv4Address
import docker
import time
import re
from loguru import logger
from dataclasses_json import config, dataclass_json
from dataclasses import dataclass, field
import threading
import time

from autoran.utils import DockerNetwork, DockerService
from autoran.utils.command_runner import RemoteRunner
from .EPCRouter import CoreRouter


# EPC Cassandra Database Service
class Cassandra(DockerService):
    def __init__(self,
                name: str,
                client: docker.APIClient,
                ip: IPv4Address,
                network: DockerNetwork):


        self.client = client
        self.ip = ip
        self.network = network
        self.name = name
        
        # create and run Cassandra container
        #cassandra_private_ip = '192.168.68.2'
        #cassandra_container = cassandra(client,private_network_dict,cassandra_private_ip)

        networking_config = client.create_networking_config({
            network.name: client.create_endpoint_config(
                ipv4_address=str(ip),
            )
        })

        self.container = client.create_container(
            image='cassandra:2.1',
            name=name,
            environment={
                "CASSANDRA_CLUSTER_NAME" : "OAI HSS Cluster" ,
                "CASSANDRA_ENDPOINT_SNITCH" : "GossipingPropertyFileSnitch",
            },
            healthcheck=docker.types.Healthcheck(
                test="/bin/bash -c \"nodetool status\"",
                interval=10*1000000000,
                timeout=5*1000000000,
                retries=5,
            ),
            networking_config=networking_config,
        )

        # start the container
        client.start(self.container)
        logger.info('{0} service successfully started at {1} with ip {2}.'.format(self.name,self.client.base_url,ip))

        #return container

        # Find next available IP address in the network
        reserved = {str(ip)}
        hosts_iterator = (host for host in network.network.hosts() if str(host) not in reserved)
        initdb_ip = next(hosts_iterator) # the first (probably .1 address which we avoid)
        initdb_ip = next(hosts_iterator) # the second

        # create and run init_db container
        #initdb_private_ip = '192.168.68.4'
        #cql_file = '/home/wlab/openair-epc-fed/component/oai-hss/src/hss_rel14/db/oai_db.cql'
        #cassandra_initdb = init_db(client, private_network_dict, initdb_private_ip, cassandra_private_ip, cql_file) 

        networking_config = client.create_networking_config({
            network.name: client.create_endpoint_config(
                ipv4_address=str(initdb_ip),
            )
        })

        initdb_container = client.create_container(
            image='cassandra_init:latest',
            name='prod-db-init',
            networking_config=networking_config,
            host_config=client.create_host_config(
                restart_policy={
                    'Name':'on-failure',
                    'MaximumRetryCount':20,
                },
            ),
            entrypoint="/bin/bash -c \"cqlsh --file /home/oai_db.cql {0} && echo 'OK'\" ".format(ip),
        )

        # start the initdb_container
        client.start(initdb_container)

        # attach(container, stdout=True, stderr=True, stream=False, logs=False, demux=False)
        # container (str) – The container to attach to.
        # stdout (bool) – Include stdout.
        # stderr (bool) – Include stderr.
        # stream (bool) – Return container output progressively as an iterator of strings, rather than a single string.
        # logs (bool) – Include the container’s previous output.
        # demux (bool) – Keep stdout and stderr separate.

        # read the logs every 1 second, if we get 'OK', we proceed
        logger.info('Waiting for Cassandra booting up...')

        success = False
        for i in range(1,20):
            time.sleep(1)
            logs = client.logs(initdb_container,stdout=True, stderr=True, tail='all')
            logs = logs.decode().rstrip()
            #print(logs)
            if "OK" in logs:
                success = True
                break
        if not success:
            logger.error('Cassandra booting up timeout.')
            raise Exception('Cassandra booting up timeout.')
    
        
        logger.info('Cassandra database has been initialized.')
        
        try:
            client.kill(initdb_container)
        except:
            pass

        try:
            client.remove_container(initdb_container)
        except:
            pass

        logger.warning('Init_db container tore down and removed.')


# HSS Service Module
class HSS(DockerService):
    def __init__(self,
                name: str,
                client: docker.APIClient,
                private_ip: IPv4Address,
                private_network: DockerNetwork,
                public_ip: IPv4Address,
                public_network: DockerNetwork,
                config: dict,
    ):

        self.name = name
        self.client = client
        self.private_ip = private_ip
        self.public_ip = public_ip
        self.private_network = private_network
        self.public_network = public_network

        networking_config = client.create_networking_config({
            private_network.name: client.create_endpoint_config(
                ipv4_address=str(private_ip),
            ),
    #       for multiple network connections, use "connect_container_to_network"
    #        public_network['name']: client.create_endpoint_config(
    #            ipv4_address=self_public_ip,
    #        ),
        })

        self.container = client.create_container(
            image='oai-hss:production',
            name=name,
            host_config=client.create_host_config(privileged=True),
            networking_config=networking_config,
            environment=config,
            healthcheck=docker.types.Healthcheck(
                test="/bin/bash -c \"pgrep oai_hss\"",
                interval=10*1000000000,
                timeout=5*1000000000,
                retries=5,
            ),
        )

        client.connect_container_to_network(self.container,public_network.name,ipv4_address=str(public_ip))

        logger.info('hss service starting...')

        # start the container
        client.start(self.container)

        success = False
        for i in range(1,10):
            time.sleep(1)
            logs = client.logs(self.container,stdout=True, stderr=True, tail='all')
            logs = logs.decode().rstrip()
            #print(logs)
            if "Started REST server" in logs:
                success = True
                break
        if not success:
            logger.error('hss booting up timeout.')
            raise Exception('hss booting up timeout.')

        logger.info('{0} service successfully started at {1} with ips {2} and {3}.'.format(self.name,self.client.base_url,public_ip, private_ip))


class MME(DockerService):
    def __init__(self,
        name: str,
        client: docker.APIClient,
        ip: IPv4Address,
        network: DockerNetwork,
        config: dict,
    ):
    
        self.name = name
        self.client = client
        self.ip = ip

        networking_config = client.create_networking_config({
            network.name: client.create_endpoint_config(
                ipv4_address=ip,
            ),
        })

        self.container = client.create_container(
            image='oai-mme:production',
            name=name,
            host_config=client.create_host_config(privileged=True),
            networking_config=networking_config,
            environment=config,
            healthcheck=docker.types.Healthcheck(
                test="/bin/bash -c \"pgrep oai_mme\"",
                interval=10*1000000000,
                timeout=5*1000000000,
                retries=5,
            ),
        )

        logger.info('MME-legacy service starting...')

        # start the container
        client.start(self.container)

        success = False
        for i in range(1,10):
            time.sleep(1)
            logs = client.logs(self.container,stdout=True, stderr=True, tail='all')
            logs = logs.decode().rstrip()
            #print(logs)
            if "Received SCTP_INIT_MSG" in logs:
                success = True
                break
        if not success:
            logger.error('MME booting up timeout.')
            raise Exception('MME booting up timeout.')

        logger.info('{0} service successfully started at {1} with ip {2}.'.format(self.name,self.client.base_url,ip))


class SPGWC(DockerService):
    def __init__(self,
        name: str,
        client: docker.APIClient, 
        network: DockerNetwork, 
        ip: IPv4Address, 
        config: dict,
    ):

        self.name = name
        self.ip = ip
        self.network = network
        self.client = client

        networking_config = client.create_networking_config({
            network.name: client.create_endpoint_config(
                ipv4_address=ip,
            ),
        })

        self.container = client.create_container(
            image='oai-spgwc:production',
            name=name,
            host_config=client.create_host_config(privileged=True),
            networking_config=networking_config,
            environment=config,
            healthcheck=docker.types.Healthcheck(
                test="/bin/bash -c \"pgrep oai_spgwc\"",
                interval=10*1000000000,
                timeout=5*1000000000,
                retries=5,
            ),
        )

        # start the container
        client.start(self.container)

        logger.info('{0} service successfully started at {1} with ip {2}.'.format(self.name,self.client.base_url,ip))

class SPGWU(DockerService):
    def __init__(self,
        name: str,
        client: docker.APIClient,
        network: IPv4Network,
        ip: IPv4Address,
        config: dict,
    ):

        self.name = name
        self.client = client
        self.network = network
        self.ip = ip

        networking_config = client.create_networking_config({
            network.name: client.create_endpoint_config(
                ipv4_address=ip,
            ),
        })

        self.container = client.create_container(
            image='oai-spgwu-tiny:production',
            name=name,
            host_config=client.create_host_config(privileged=True),
            networking_config=networking_config,
            environment=config,
            healthcheck=docker.types.Healthcheck(
                test="/bin/bash -c \"pgrep oai_spgwu\"",
                interval=10*1000000000,
                timeout=5*1000000000,
                retries=5,
            ),
        )

        # start the container
        client.start(self.container)
        logger.info('{0} service successfully started at {1} with ip {2}.'.format(self.name,self.client.base_url,ip))


class LogsCheckerThread (threading.Thread):
    def __init__(self, threadID, name, client, container, line_based, events_keys, epc):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.client = client
        self.container = container
        self._kill = threading.Event()
        self._interval = 0.1
        self.line_based = line_based
        self.events_keys = events_keys
        self.epc = epc

    def run(self):
        logger.info('Thread {0} successfully started at {1}.'.format(self.name,self.client.base_url))
       
        events_keys = self.events_keys
        complete_logs = ''
        while True:
            is_killed = self._kill.wait(self._interval)
            if is_killed:
                break

            new_complete_logs = self.client.logs(self.container, stdout=True, stderr=True, tail='all').decode()
            logs = new_complete_logs.replace(complete_logs,'',1)
            complete_logs = new_complete_logs

            if logs:
                #print(logs)
                events_results = {}
                for event in events_keys:
                    if self.line_based:
                        lines = logs.splitlines()
                        for line in lines:
                            for ele in events_keys[event]:
                                if ele in line:
                                    if event not in events_results:
                                        events_results[event] = {}
                                    events_results[event][events_keys[event][ele][1]] = line.split()[events_keys[event][ele][0]]
                    else:
                        if events_keys[event]['main_key'] in logs:
                            for ele in events_keys[event]['sub_keys']:
                                result = re.search(ele+'(.*)'+'\n', logs)
                                if event not in events_results:
                                    events_results[event] = {}
                                events_results[event][events_keys[event]['sub_keys'][ele][1]] = result.group(1).strip()

                if events_results:
                    self.epc.handle_event(events_results)
                    #logger.info(events_results)

        logger.warning('Thread {0} stopped at {1}.'.format(self.name,self.client.base_url))

    def kill(self):
        self._kill.set()


class EvolvedPacketCore():
    def __init__(self,
            host: str,
            private_network: DockerNetwork,
            public_network: DockerNetwork,
        ):

        # connect to the EPC host dockerhub
        self.epc_host_name = host
        self.docker_port = '2375'
        logger.info('Starting LTE evolved packet core (EPC) on {0} port {1}.'.format(self.epc_host_name,self.docker_port))
        self.client = docker.APIClient(base_url=self.epc_host_name+':'+self.docker_port)
    
        self.docker_private_network = private_network
        # figure out private ips
        self.cassandra_private_ip = private_network.allocate_ip()
        self.hss_private_ip = private_network.allocate_ip()

        self.docker_public_network = public_network
        # figure out public ips
        self.hss_public_ip = public_network.allocate_ip()
        self.mme_public_ip = public_network.allocate_ip()
        self.spgwc_public_ip = public_network.allocate_ip()
        self.spgwu_public_ip = public_network.allocate_ip()

        # prepare ue and enb lists
        self.connected_ues = {};
        self.connected_enbs = {};

        # prepare the remote runner
        self.rr = RemoteRunner(
            client=self.client,
            name='prod-remoterunner',
        )

        self.epc_router = None
        self.threads_running = False
        self.spgwu = None
        self.spgwc = None
        self.mme = None
        self.hss = None
        self.cassandra = None


    def handle_event(self,event):

        event_str = list(event.keys())[0]
        if event_str == 'ue_attached_mme':
            imsi = event[event_str]['imsi']
            logger.info("MME verified a UE with IMSI {0} for attaching the EPC at {1}".format(imsi,self.client.base_url))

        elif event_str == 'ue_attached_spgwc':
            imsi = event[event_str]['imsi']
            ip = event[event_str]['ip']

            if imsi in self.connected_ues.keys():
                logger.info("A UE with IMSI {0} attached to the EPC at {1} and got ip {2} again, no routing.".format(imsi,self.client.base_url,ip))
            else:

                # Get the router to start GRE tunnel
                tunnel_name = self.epc_router.create_tunnel(
                    remote_ip=ip,
                    local_ip=self.docker_public_network.docker_bridge_ip,
                    tunnel_epc_if=str(self.routing_config[imsi]['epc_tun_if']),
                )
                
                self.connected_ues[imsi] = { 'ip':ip, 'tunnel':tunnel_name }
                logger.info("A UE with IMSI {0} attached to the EPC at {1} and got ip {2}".format(imsi,self.client.base_url,ip))
                
                logger.info("Waiting for EPC {0} tunnel handshake with UE {1}...".format(self.client.base_url,imsi))
                tunnel_handshake = self.epc_router.wait_for_tunnel(
                    tunnel_ue_ip=str(self.routing_config[imsi]['ue_tun_if'].ip),
                )
                if not tunnel_handshake:
                    logger.error("EPC at {0} could not handshake over the tunnel with UE with imsi {1}.".format(self.client.base_url,imsi))
                else:
                    logger.info("EPC at {0} successfully tested gre tunnel with UE with imsi {1}.".format(self.client.base_url,imsi))

                    # Expose UE external network
                    self.epc_router.create_tunnel_route(
                        tunnel_name=tunnel_name,
                        target_net=str(self.routing_config[imsi]['ue_ex_net']),
                        ue_tunnel_ip=str(self.routing_config[imsi]['ue_tun_if'].ip),
                    )
                    
                    logger.info("EPC at {0} successfully added a route from {1} to UE {2} external network {3}.".format(self.client.base_url,tunnel_name,imsi,str(self.routing_config[imsi]['ue_ex_net'])))

                    self.epc_router.enable_iptables_forwarding(tunnel_name)


        elif event_str == 'ue_detached':
            imsi = event[event_str]['imsi']
            ip = event[event_str]['ip']
            logger.warning("UE with IMSI {0} disconnected from the EPC at {1} with ip {2}".format(imsi,self.client.base_url,ip))

            # Delete tunnel route
            self.epc_router.remove_tunnel_route(
                target_net=str(self.routing_config[imsi]['ue_ex_net']),
            )

            # Get the router to delete GRE tunnel
            tunnel_name = self.connected_ues[imsi]['tunnel']
            self.epc_router.remove_tunnel(
                name=tunnel_name,
            )
            
            # delete ue from the list
            del self.connected_ues[imsi]
            
        elif event_str == 'eNB_attached':
            enb_id = event[event_str]['enb_id']
            assoc_id = event[event_str]['assoc_id']
            self.connected_enbs[assoc_id] = { 'enb_id':enb_id }
            logger.info("Enodeb with id {0} connected to the EPC at {1} with association id {2}".format(enb_id,self.client.base_url,assoc_id))

        elif event_str == 'eNB_detached':
            assoc_id = event[event_str]['assoc_id']
            enb_id = self.connected_enbs[assoc_id]['enb_id']
            logger.warning("Enodeb with id {0} disconnected from the EPC at {1} with association id {2}".format(enb_id,self.client.base_url,assoc_id))
            del self.connected_enbs[assoc_id]

        

    def start(self,
        hss_config: dict,
        mme_config: dict,
        spgwc_config: dict,
        spgwu_config: dict,
        routing_config: dict,
    ):
        
        self.cassandra = Cassandra(
            name='prod-cassandra',
            client=self.client,
            ip=IPv4Address(self.cassandra_private_ip),
            network=self.docker_private_network,
        )

        self.hss = HSS(
            name='prod-oai-hss',
            client=self.client,
            private_network=self.docker_private_network,
            public_network=self.docker_public_network,
            private_ip=IPv4Address(self.hss_private_ip),
            public_ip=IPv4Address(self.hss_public_ip),
            config=hss_config,
        )

        self.mme = MME(
            name='prod-oai-legacy-mme',
            client=self.client,
            network=self.docker_public_network,
            ip=self.mme_public_ip,
            config=mme_config,
        )

        self.spgwc = SPGWC(
            name='prod-oai-spgwc',
            client=self.client,
            network=self.docker_public_network,
            ip=self.spgwc_public_ip,
            config=spgwc_config,
        )

        self.spgwu = SPGWU(
            name='prod-oai-spgwu-tiny',
            client=self.client,
            network=self.docker_public_network,
            ip=self.spgwu_public_ip,
            config=spgwu_config,
        )
       
        self.routing_config = routing_config

        # initiate CoreRouter
        self.epc_router = CoreRouter(
            client=self.client,
            ue_network='12.1.1.0/24',
            spgwu_public_ip=self.spgwu_public_ip, 
            public_bridge_ip=self.docker_public_network.docker_bridge_ip,
            remote_runner=self.rr,
            routing_config=routing_config,
        )

        # start threads
        mme_events_keys = {
            'eNB_attached':{
                'Adding eNB id':(-7,'enb_id'),
                'Create eNB context':(-1,'assoc_id'),
            },
            'eNB_detached':{
                'Sending close connection':(-1,'assoc_id'),
            },
            'ue_attached_mme': {
                'MME_APP context for ue_id':(-2,'imsi'),
            }
        }
        # start mme connection observer  
        self.mme_checker_thread = LogsCheckerThread(
            threadID = 1, 
            name = "MME-logs-checker-thread", 
            client = self.client, 
            container = self.mme.container, 
            line_based = True,
            events_keys = mme_events_keys,
            epc = self,
        )
        self.mme_checker_thread.start()

        spgwc_events_keys = {
            'ue_attached_spgwc':{
                'main_key':'Sending ITTI message MODIFY_BEARER_RESPONSE',
                'sub_keys':{
                    'IMSI:':(1,'imsi'),
                    'PAA IPv4:':(1,'ip'),
                },
            },
            'ue_detached':{
                'main_key':'Sending ITTI message RELEASE_ACCESS_BEARERS_RESPONSE',
                'sub_keys':{
                    'IMSI:':(1,'imsi'),
                    'PAA IPv4:':(1,'ip'),
                },
            }
        }
        # start spgwc connection observer
        self.spgwc_checker_thread = LogsCheckerThread(
            threadID = 2,
            name = "SPGWC-logs-checker-thread",
            client = self.client,
            container = self.spgwc.container,
            line_based = False,
            events_keys = spgwc_events_keys,
            epc = self,
        )
        self.spgwc_checker_thread.start()
        
        self.threads_running = True

    def stop(self):

        if self.epc_router:
            self.epc_router.__del__()
        
        if self.threads_running:
            self.spgwc_checker_thread.kill()
            self.mme_checker_thread.kill()
            self.spgwc_checker_thread.join()
            self.mme_checker_thread.join()
            self.threads_running = False
        
        if self.spgwu:
            self.spgwu.__del__()

        if self.spgwc:
            self.spgwc.__del__()

        if self.mme:
            self.mme.__del__()

        if self.hss:
            self.hss.__del__()

        if self.cassandra:
            self.cassandra.__del__()

    def __del__(self):
        self.stop()

if __name__ == "__main__":

    # connect to the EPC host dockerhub
    epc_host_name = 'finarfin'
    docker_port = '2375'
    logger.info('Starting LTE evolved packet core (EPC) on {0} port {1}.'.format(epc_host_name,docker_port))
    client = docker.APIClient(base_url=epc_host_name+':'+docker_port)
    
    # create networks
    private_network = DockerNetwork(client,IPv4Network('192.168.68.0/26'),'prod-oai-private-net')
    public_network = DockerNetwork(client,IPv4Network('192.168.61.192/26'),'prod-oai-public-net')

    cassandra_private_ip = '192.168.68.2'
    cassandra = Cassandra(
        name='prod-cassandra',
        client=client,
        ip=IPv4Address(cassandra_private_ip),
        network=private_network,
    )

    # create and run hss container
    hss_private_ip = '192.168.68.3'
    hss_public_ip = '192.168.61.194'
    hss_config={
        "TZ": "Europe/Paris",
        "REALM": "openairinterface.org",
        "HSS_FQDN": "hss.openairinterface.org",
        "PREFIX": "/openair-hss/etc",
        "cassandra_Server_IP": cassandra_private_ip,
        "OP_KEY": "63bfa50ee6523365ff14c1f45f88737d",
        "LTE_K": "0c0a34601d4f07677303652c0462535b",
        "APN1": "oai.ipv4",
        "APN2": "oai2.ipv4",
        "FIRST_IMSI": "208960010000001",
        "NB_USERS": "5",
    }
    hss = HSS(
        name='prod-oai-hss',
        client=client, 
        private_network=private_network, 
        public_network=public_network, 
        private_ip=IPv4Address(hss_private_ip), 
        public_ip=IPv4Address(hss_public_ip), 
        config=hss_config,
    )

    # create and run mme container
    mme_public_ip = '192.168.61.195'
    spgwc_public_ip = '192.168.61.196'
    mme_config={
        "TZ": "Europe/Paris",
        "REALM": "openairinterface.org",
        "PREFIX": "/openair-mme/etc",
        "INSTANCE": 1,
        "PID_DIRECTORY": "/var/run",
        "HSS_IP_ADDR": hss_public_ip,
        "HSS_HOSTNAME": 'hss',
        "HSS_FQDN": "hss.openairinterface.org",
        "HSS_REALM": "openairinterface.org",
        'MCC': '208',
        'MNC': '96',
        'MME_GID': 32768,
        'MME_CODE': 3,
        'TAC_0': 1,
        'TAC_1': 2,
        'TAC_2': 3,
        'MME_FQDN': 'mme.openairinterface.org',
        'MME_S6A_IP_ADDR': mme_public_ip,
        'MME_INTERFACE_NAME_FOR_S1_MME': 'eth0',
        'MME_IPV4_ADDRESS_FOR_S1_MME': mme_public_ip,
        'MME_INTERFACE_NAME_FOR_S11': 'eth0',
        'MME_IPV4_ADDRESS_FOR_S11': mme_public_ip,
        'MME_INTERFACE_NAME_FOR_S10': 'lo',
        'MME_IPV4_ADDRESS_FOR_S10': '127.0.0.10',
        'OUTPUT': 'CONSOLE',
        'SGW_IPV4_ADDRESS_FOR_S11_0': spgwc_public_ip,
        'PEER_MME_IPV4_ADDRESS_FOR_S10_0': '0.0.0.0',
        'PEER_MME_IPV4_ADDRESS_FOR_S10_1': '0.0.0.0',
        'MCC_SGW_0': '208',
        'MNC3_SGW_0': '096',
        'TAC_LB_SGW_0': '01',
        'TAC_HB_SGW_0': '00',
        'MCC_MME_0': '208',
        'MNC3_MME_0': '096',
        'TAC_LB_MME_0': '02',
        'TAC_HB_MME_0': '00',
        'MCC_MME_1': '208',
        'MNC3_MME_1': '096',
        'TAC_LB_MME_1': '03',
        'TAC_HB_MME_1': '00',
        'TAC_LB_SGW_TEST_0': '03',
        'TAC_HB_SGW_TEST_0': '00',
        'SGW_IPV4_ADDRESS_FOR_S11_TEST_0': '0.0.0.0',
    }
    mme = MME(
        name='prod-oai-legacy-mme',
        client=client, 
        network=public_network, 
        ip=mme_public_ip,
        config=mme_config,
    )

    

    spgwc_config = {
        'TZ': 'Europe/Paris',
        'SGW_INTERFACE_NAME_FOR_S11': 'eth0',
        'PGW_INTERFACE_NAME_FOR_SX': 'eth0',
        'DEFAULT_DNS_IPV4_ADDRESS': '192.168.18.129',
        'DEFAULT_DNS_SEC_IPV4_ADDRESS': '8.8.4.4',
        'PUSH_PROTOCOL_OPTION': 'true',
        'APN_NI_1': 'oai.ipv4',
        'APN_NI_2': 'oai2.ipv4',
        'DEFAULT_APN_NI_1': 'oai.ipv4',
        'UE_IP_ADDRESS_POOL_1': '12.1.1.2 - 12.1.1.254',
        'UE_IP_ADDRESS_POOL_2': '12.0.0.2 - 12.0.0.254',
        'MCC': '208',
        'MNC': '96',
        'MNC03': '096',
        'TAC': 1,
        'GW_ID': 1,
        'REALM': 'openairinterface.org',
    }
    spgwc = SPGWC(
        name='prod-oai-spgwc',
        client=client, 
        network=public_network, 
        ip=spgwc_public_ip,
        config=spgwc_config,
    )

    spgwu_public_ip = '192.168.61.197'
    spgwu_config = {
        'TZ': 'Europe/Paris',
        'PID_DIRECTORY': '/var/run',
        'INSTANCE': 1,
        'SGW_INTERFACE_NAME_FOR_S1U_S12_S4_UP': 'eth0',
        'PGW_INTERFACE_NAME_FOR_SGI': 'eth0',
        'SGW_INTERFACE_NAME_FOR_SX': 'eth0',
        'SPGWC0_IP_ADDRESS': spgwc_public_ip,
        'NETWORK_UE_IP': '12.1.1.0/24',
        'NETWORK_UE_NAT_OPTION': 'yes',
        'MCC': '208',
        'MNC': '96',
        'MNC03': '096',
        'TAC': 1,
        'GW_ID': 1,
        'REALM': 'openairinterface.org',
    }
    spgwu = SPGWU(
        name='prod-oai-spgwu-tiny',
        client=client, 
        network=public_network, 
        ip=spgwu_public_ip,
        config=spgwu_config,
    )

    input("Press any key to continue...")

    spgwu.__del__()
    spgwc.__del__()
    mme.__del__()
    hss.__del__()
    cassandra.__del__()
    private_network.__del__()
    public_network.__del__()

