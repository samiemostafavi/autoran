from ipaddress import IPv4Interface, IPv4Network, IPv4Address
import docker
import time
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

        ipam_pool = docker.types.IPAMPool(
            subnet=str(network),
        )
        ipam_config = docker.types.IPAMConfig(
            pool_configs=[ipam_pool]
        )
        self.docker_network_dict = client.create_network(name,ipam=ipam_config)
        self.network = network
        self.name = name

    def __del__(self):
            
        logger.warning("Removing docker network {0} {1}.".format(self.name,str(self.network)))
        try:
            client.remove_network(self.docker_network_dict['Id'])
        except:
            pass


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
            client.kill(self.container)
        except:
            pass

        try:
            client.remove_container(self.container)
        except:
            pass


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

