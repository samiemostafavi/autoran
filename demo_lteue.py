import docker
import time
from loguru import logger

from lib.utils import DockerNetwork, DockerService
from lib.lte_py.ue import LTEUE

if __name__ == "__main__":

    # connect to the EPC host dockerhub
    docker_host_name = 'fingolfin'
    docker_port = '2375'
    logger.info('Starting LTE UE on {0} port {1}.'.format(docker_host_name,docker_port))
    client = docker.APIClient(base_url=docker_host_name+':'+docker_port)

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
    lteue = LTEUE(
        name='prod-oai-lte-ue',
        client=client, 
        config=ue_config,
    )
    
    input("Press any key to stop...")

    lteue.__del__()

