from ipaddress import IPv4Interface, IPv4Network, IPv4Address
import docker
import time
from loguru import logger
from dataclasses_json import config, dataclass_json
from dataclasses import dataclass, field

from lib.lte_py.epc import *
from lib.lte_py.enodeb import ENodeB
from lib.utils import *

if __name__ == "__main__":

    # connect to the EPC host dockerhub
    epc_host_name = 'finarfin'

    epc = EvolvedPacketCore(
            host=epc_host_name,
            private_network='192.168.68.0/26',
            public_network='192.168.61.192/26',
    )

    # create hss config
    hss_config={
        "TZ": "Europe/Paris",
        "REALM": "openairinterface.org",
        "HSS_FQDN": "hss.openairinterface.org",
        "PREFIX": "/openair-hss/etc",
        "cassandra_Server_IP": epc.cassandra_private_ip,
        "OP_KEY": "63bfa50ee6523365ff14c1f45f88737d",
        "LTE_K": "0c0a34601d4f07677303652c0462535b",
        "APN1": "oai.ipv4",
        "APN2": "oai2.ipv4",
        "FIRST_IMSI": "208960010000001",
        "NB_USERS": "5",
    }

    # create mme config
    mme_config={
        "TZ": "Europe/Paris",
        "REALM": "openairinterface.org",
        "PREFIX": "/openair-mme/etc",
        "INSTANCE": 1,
        "PID_DIRECTORY": "/var/run",
        "HSS_IP_ADDR": epc.hss_public_ip,
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
        'MME_S6A_IP_ADDR': epc.mme_public_ip,
        'MME_INTERFACE_NAME_FOR_S1_MME': 'eth0',
        'MME_IPV4_ADDRESS_FOR_S1_MME': epc.mme_public_ip,
        'MME_INTERFACE_NAME_FOR_S11': 'eth0',
        'MME_IPV4_ADDRESS_FOR_S11': epc.mme_public_ip,
        'MME_INTERFACE_NAME_FOR_S10': 'lo',
        'MME_IPV4_ADDRESS_FOR_S10': '127.0.0.10',
        'OUTPUT': 'CONSOLE',
        'SGW_IPV4_ADDRESS_FOR_S11_0': epc.spgwc_public_ip,
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

    # create spgwc config
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

    # create spgwu config
    spgwu_config = {
        'TZ': 'Europe/Paris',
        'PID_DIRECTORY': '/var/run',
        'INSTANCE': 1,
        'SGW_INTERFACE_NAME_FOR_S1U_S12_S4_UP': 'eth0',
        'PGW_INTERFACE_NAME_FOR_SGI': 'eth0',
        'SGW_INTERFACE_NAME_FOR_SX': 'eth0',
        'SPGWC0_IP_ADDRESS': epc.spgwc_public_ip,
        'NETWORK_UE_IP': '12.1.1.0/24',
        'NETWORK_UE_NAT_OPTION': 'yes',
        'MCC': '208',
        'MNC': '96',
        'MNC03': '096',
        'TAC': 1,
        'GW_ID': 1,
        'REALM': 'openairinterface.org',
    }

    # create routing config
    routing_config = {
        '208960010000001':{
            'epc_tun_if' : IPv4Interface('172.17.0.1/24'),
            'ue_tun_if' : IPv4Interface('172.17.0.2/24'),
            'ue_ex_net' : IPv4Network('10.0.1.0/24'),
        },
    }

    epc.start(hss_config,mme_config,spgwc_config,spgwu_config, routing_config)

    # start an internal enb
    enb_public_ip = epc.allocate_public_ip()
    enb_config = {
        "mme_ip":epc.mme_public_ip,
        "spgwc_ip":epc.spgwc_public_ip,
        "USE_FDD_MONO": 1,
        "USE_B2XX": 1,
        'ENB_NAME':'eNB-Eurecom-LTEBox',
        'TAC':1,
        'MCC':208,
        'MNC':96,
        'MNC_LENGTH':2,
        'RRC_INACTIVITY_THRESHOLD':30,
        'UTRA_BAND_ID':7,
        'DL_FREQUENCY_IN_MHZ':2680,
        'UL_FREQUENCY_OFFSET_IN_MHZ':120,
        'NID_CELL':0,
        'NB_PRB':25,
        'ENABLE_MEASUREMENT_REPORTS':'yes',
        'MME_S1C_IP_ADDRESS':epc.mme_public_ip,
        'ENABLE_X2':'yes',
        'ENB_X2_IP_ADDRESS':enb_public_ip,
        'ENB_S1C_IF_NAME':'eth0',
        'ENB_S1C_IP_ADDRESS':enb_public_ip,
        'ENB_S1U_IF_NAME':'eth0',
        'ENB_S1U_IP_ADDRESS':enb_public_ip,
        'THREAD_PARALLEL_CONFIG':'PARALLEL_SINGLE_THREAD',
        'FLEXRAN_ENABLED':'no',
        'FLEXRAN_INTERFACE_NAME':'eth0',
        'FLEXRAN_IPV4_ADDRESS':'CI_FLEXRAN_CTL_IP_ADDR',
    }
    enb = ENodeB(
        name='prod-oai-enb',
        client=epc.client,
        network=epc.docker_public_network,
        ip=enb_public_ip,
        config=enb_config,
    )

    input("Press any key to stop...\n")

    enb.__del__()
    epc.stop()
    epc.__del__()


