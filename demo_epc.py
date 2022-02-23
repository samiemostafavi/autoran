from ipaddress import IPv4Interface, IPv4Network, IPv4Address
import docker
import time
from loguru import logger
from dataclasses_json import config, dataclass_json
from dataclasses import dataclass, field

from autoran.oailte.epc import *
from autoran.utils import *

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

