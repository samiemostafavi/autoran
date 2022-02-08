import docker
import time
from loguru import logger

def cassandra(client, network, ip):

    networking_config = client.create_networking_config({
        network['name']: client.create_endpoint_config(
            ipv4_address=ip,
        )
    })

    container = client.create_container(
        image='cassandra:2.1',
        name='prod-cassandra',
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
    client.start(container)

    logger.info('Cassandra service successfully started at {0} with ip {1}.'.format(network['name'],ip))

    return container

    # attach(container, stdout=True, stderr=True, stream=False, logs=False, demux=False)
    # container (str) – The container to attach to.
    # stdout (bool) – Include stdout.
    # stderr (bool) – Include stderr.
    # stream (bool) – Return container output progressively as an iterator of strings, rather than a single string.
    # logs (bool) – Include the container’s previous output.
    # demux (bool) – Keep stdout and stderr separate.

    # read the logs live
    #dkg = client.attach(container, stdout=True, stderr=True, stream=True, logs=True, demux=False)
    #for line in dkg:
    #    line_out = line.decode()
    #    print(line_out)
    
    #logs = client.attach(container, stdout=True, stderr=True, stream=False, logs=True, demux=False)
    #print(logs.decode())

def init_db(client, network, self_ip, db_ip, cql_file):

    networking_config = client.create_networking_config({
        network['name']: client.create_endpoint_config(
            ipv4_address=self_ip,
        )
    })

    container = client.create_container(
        image='cassandra:2.1',
        name='prod-db-init',
        networking_config=networking_config,
        volumes=['/home/oai_db.cql'],
        host_config=client.create_host_config(binds=[ 
                '{0}:/home/oai_db.cql'.format(cql_file),
            ],restart_policy={
                'Name':'on-failure',
                'MaximumRetryCount':20,
            },
        ),
        entrypoint="/bin/bash -c \"cqlsh --file /home/oai_db.cql {0} && echo 'OK'\" ".format(db_ip),
    )

    # start the container
    client.start(container)

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
        logs = client.logs(container,stdout=True, stderr=True, tail='all')
        logs = logs.decode().rstrip()
        #print(logs)
        if "OK" in logs:
            success = True
            break
    if not success:
        logger.error('Cassandra booting up timeout.')
        raise Exception('Cassandra booting up timeout.')

    #    try:
    #        dkg = client.attach(container, stdout=True, stderr=True, stream=True, logs=True, demux=False)
    #        line = next(dkg)
    #        line_out = line.decode()
    #        print(line_out.rstrip())
    #        if "OK" in line_out:
    #            break
    #    except:
    #        pass

    logger.info('Cassandra database has been initialized.')

    return container
    
    #logs = client.attach(container, stdout=True, stderr=True, stream=False, logs=True, demux=False)
    #print(logs.decode())

def hss(client, private_network, public_network, self_private_ip, self_public_ip, db_ip):

    networking_config = client.create_networking_config({
        private_network['name']: client.create_endpoint_config(
            ipv4_address=self_private_ip,
        ),
#       for multiple network connections, use "connect_container_to_network"
#        public_network['name']: client.create_endpoint_config(
#            ipv4_address=self_public_ip,
#        ),
    })

    container = client.create_container(
        image='oai-hss:production',
        name='prod-oai-hss',
        host_config=client.create_host_config(privileged=True),
        networking_config=networking_config,
        environment={
            "TZ": "Europe/Paris",
            "REALM": "openairinterface.org",
            "HSS_FQDN": "hss.openairinterface.org",
            "PREFIX": "/openair-hss/etc",
            "cassandra_Server_IP": db_ip,
            "OP_KEY": "63bfa50ee6523365ff14c1f45f88737d",
            "LTE_K": "0c0a34601d4f07677303652c0462535b",
            "APN1": "oai.ipv4",
            "APN2": "oai2.ipv4",
            "FIRST_IMSI": "208960010000001",
            "NB_USERS": "5",
        },
        healthcheck=docker.types.Healthcheck(
            test="/bin/bash -c \"pgrep oai_hss\"",
            interval=10*1000000000,
            timeout=5*1000000000,
            retries=5,
        ),
    )

    client.connect_container_to_network(container,public_network['name'],ipv4_address=self_public_ip)

    # start the container
    client.start(container)

    logger.info('HSS service successfully started at {0} with ip {1} and {2} with ip {3}.'.format(private_network['name'],self_private_ip,public_network['name'],self_public_ip))
    
    return container

def mme(client, public_network, self_public_ip, hss_public_ip, spgwc_public_ip):

    networking_config = client.create_networking_config({
        public_network['name']: client.create_endpoint_config(
            ipv4_address=self_public_ip,
        ),
    })

    container = client.create_container(
        image='oai-mme:production',
        name='prod-oai-mme',
        host_config=client.create_host_config(privileged=True),
        networking_config=networking_config,
        environment={
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
            'MME_S6A_IP_ADDR': self_public_ip,
            'MME_INTERFACE_NAME_FOR_S1_MME': 'eth0',
            'MME_IPV4_ADDRESS_FOR_S1_MME': self_public_ip,
            'MME_INTERFACE_NAME_FOR_S11': 'eth0',
            'MME_IPV4_ADDRESS_FOR_S11': self_public_ip,
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
        },
        healthcheck=docker.types.Healthcheck(
            test="/bin/bash -c \"pgrep oai_mme\"",
            interval=10*1000000000,
            timeout=5*1000000000,
            retries=5,
        ),
    )

    # start the container
    client.start(container)

    logger.info('MME-legacy service successfully started at {0} with ip {1}.'.format(public_network['name'],self_public_ip))

    return container

def spgwc(client, public_network, self_public_ip):

    networking_config = client.create_networking_config({
        public_network['name']: client.create_endpoint_config(
            ipv4_address=self_public_ip,
        ),
    })

    container = client.create_container(
        image='oai-spgwc:production',
        name='prod-oai-spgwc',
        host_config=client.create_host_config(privileged=True),
        networking_config=networking_config,
        environment={
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
        },
        healthcheck=docker.types.Healthcheck(
            test="/bin/bash -c \"pgrep oai_spgwc\"",
            interval=10*1000000000,
            timeout=5*1000000000,
            retries=5,
        ),
    )

    # start the container
    client.start(container)

    logger.info('SPGWC service successfully started at {0} with ip {1}.',public_network['name'],self_public_ip)

    return container


def spgwu(client, public_network, self_public_ip, spgwc_ip):

    networking_config = client.create_networking_config({
        public_network['name']: client.create_endpoint_config(
            ipv4_address=self_public_ip,
        ),
    })

    container = client.create_container(
        image='oai-spgwu-tiny:production',
        name='prod-oai-spgwu-tiny',
        host_config=client.create_host_config(privileged=True),
        networking_config=networking_config,
        environment={
            'TZ': 'Europe/Paris',
            'PID_DIRECTORY': '/var/run',
            'INSTANCE': 1,
            'SGW_INTERFACE_NAME_FOR_S1U_S12_S4_UP': 'eth0',
            'PGW_INTERFACE_NAME_FOR_SGI': 'eth0',
            'SGW_INTERFACE_NAME_FOR_SX': 'eth0',
            'SPGWC0_IP_ADDRESS': spgwc_ip,
            'NETWORK_UE_IP': '12.1.1.0/24',
            'NETWORK_UE_NAT_OPTION': 'yes',
            'MCC': '208',
            'MNC': '96',
            'MNC03': '096',
            'TAC': 1,
            'GW_ID': 1,
            'REALM': 'openairinterface.org',
        },
        healthcheck=docker.types.Healthcheck(
            test="/bin/bash -c \"pgrep oai_spgwu\"",
            interval=10*1000000000,
            timeout=5*1000000000,
            retries=5,
        ),
    )

    # start the container
    client.start(container)

    logger.info('SPGWU-tiny service successfully started at {0} with ip {1}.',public_network['name'],self_public_ip)

    return container


if __name__ == "__main__":

    # connect to the EPC host dockerhub
    #client = DockerClient(base_url='192.168.2.2:2375');
    #client = docker.APIClient(base_url='192.168.2.2:2375')
    docker_host_name = 'finarfin'
    docker_port = '2375'
    private_network_dict = { 'name':'prod-oai-private-net', 'subnet':'192.168.68.0/26' }
    public_network_dict = { 'name':'prod-oai-public-net', 'subnet':'192.168.61.192/26' }

    logger.info('Starting LTE evolved packet core (EPC) on {0} port {1}.'.format(docker_host_name,docker_port))
    client = docker.APIClient(base_url=docker_host_name+':'+docker_port)

    # create prod-oai-private-net
    ipam_pool_private = docker.types.IPAMPool(
        subnet= private_network_dict['subnet'],
    )
    ipam_config_private = docker.types.IPAMConfig(
        pool_configs=[ipam_pool_private]
    )
    private_network = client.create_network(private_network_dict['name'],ipam=ipam_config_private)

    # create prod-oai-public-net
    ipam_pool_public = docker.types.IPAMPool(
        subnet=public_network_dict['subnet'],
    )
    ipam_config_public = docker.types.IPAMConfig(
        pool_configs=[ipam_pool_public]
    )
    public_network = client.create_network(public_network_dict['name'],ipam=ipam_config_public)

    # create and run Cassandra container
    cassandra_private_ip = '192.168.68.2'
    cassandra_container = cassandra(client,private_network_dict,cassandra_private_ip)

    # create and run init_db container
    initdb_private_ip = '192.168.68.4'
    cql_file = '/home/wlab/openair-epc-fed/component/oai-hss/src/hss_rel14/db/oai_db.cql'
    cassandra_initdb = init_db(client, private_network_dict, initdb_private_ip, cassandra_private_ip, cql_file) 

    try:
        client.kill(cassandra_initdb)
    except:
        pass

    try:
        client.remove_container(cassandra_initdb)
    except:
        pass

    logger.warning('Init_db container tore down and removed.')

    
    # create and run hss container
    hss_private_ip = '192.168.68.3'
    hss_public_ip = '192.168.61.194'
    hss_container = hss(client, private_network_dict, public_network_dict, hss_private_ip, hss_public_ip, cassandra_private_ip)


    # create and run mme container
    mme_public_ip = '192.168.61.195'
    spgwc_public_ip = '192.168.61.196'
    mme_container = mme(client, public_network_dict, mme_public_ip, hss_public_ip, spgwc_public_ip)
    
    spgwc_container = spgwc(client, public_network_dict, spgwc_public_ip)

    spgwu_public_ip = '192.168.61.197'
    spgwu_container = spgwu(client, public_network_dict, spgwu_public_ip ,spgwc_public_ip)

    input("Press any key to continue...")

    try:
        client.kill(spgwu_container)
    except:
        pass

    try:
        client.remove_container(spgwu_container)
    except:
        pass


    try:
        client.kill(spgwc_container)
    except:
        pass

    try:
        client.remove_container(spgwc_container)
    except:
        pass


    try:
        client.kill(mme_container)
    except:
        pass

    try:
        client.remove_container(mme_container)
    except:
        pass


    try:
        client.kill(hss_container)
    except:
        pass

    try:
        client.remove_container(hss_container)
    except:
        pass

    try:
        client.kill(cassandra_container)
    except:
        pass

    try:    
        client.remove_container(cassandra_container)
    except:
        pass

    try:
        client.remove_network(private_network['Id'])
        client.remove_network(public_network['Id'])
    except:
        pass

