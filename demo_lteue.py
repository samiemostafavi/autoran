import docker
import time
from loguru import logger

from autoran.utils import DockerNetwork, DockerService
from autoran.oailte.ue import LTEUE
from ipaddress import IPv4Interface, IPv4Network, IPv4Address 

if __name__ == "__main__":

    # connect to the EPC host dockerhub
    docker_host_name = 'fingolfin'

    # create and run ue container
    ue_config = {
        "PLMN_FULLNAME":"OpenAirInterface",
        "PLMN_SHORTNAME":"OAICN",
        "PLMN_CODE":"20896",
        "MCC":"208",
        "MNC":"96",
        "IMEI":"356113022094149",
        "MSIN":"0010000001",
        "USIM_API_K":"0c0a34601d4f07677303652c0462535b",
        "OPC":"ba05688178e398bedc100674071002cb",
        "MSISDN":"33611123456",
        'DL_FREQUENCY_IN_MHZ':2680,
        'NB_PRB':25,
        'RX_GAIN':120,
        'TX_GAIN':0,
        'MAX_POWER':0,
    }

    routing_config = {
        'epc_tun_if' : IPv4Interface('192.17.0.1/24'),
        'ue_tun_if' : IPv4Interface('192.17.0.2/24'),
        'epc_ex_net' : IPv4Network('10.4.0.0/24'),
        'ue_ex_net_if': 'enp4s0',
    }

    lteue = LTEUE(
        name='prod-oai-lte-ue',
        host=docker_host_name, 
        config=ue_config,
        routing_config=routing_config,
    )


    
    input("Press any key to stop...")

    lteue.__del__()

