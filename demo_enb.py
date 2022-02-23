from ipaddress import IPv4Interface, IPv4Network, IPv4Address
import docker
import time
from loguru import logger
from dataclasses_json import config, dataclass_json
from dataclasses import dataclass, field

from autoran.utils import DockerNetwork, DockerService
from autoran.oailte.enodeb import ENodeB

if __name__ == "__main__":

    # connect to the EPC host dockerhub
    docker_host_name = 'finarfin'
    docker_port = '2375'
    logger.info('Starting LTE eNodeB on {0} port {1}.'.format(docker_host_name,docker_port))
    client = docker.APIClient(base_url=docker_host_name+':'+docker_port)
   
    # creating or fetching network
    public_network = DockerNetwork(client,IPv4Network('192.168.61.192/26'),'prod-oai-public-net')

    # create and run enb container
    mme_public_ip = '192.168.61.195'
    spgwc_public_ip = '192.168.61.196'
    enb_public_ip = '192.168.61.198'
    enb_config = {
        "mme_ip":mme_public_ip,
        "spgwc_ip":spgwc_public_ip,
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
        'MME_S1C_IP_ADDRESS':mme_public_ip,
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
        client=client,
        network=public_network,
        ip=enb_public_ip, 
        config=enb_config,
    )

    input("Press any key to continue...")

    enb.__kill__()
    
