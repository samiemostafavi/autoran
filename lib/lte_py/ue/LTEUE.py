import docker
import time
from loguru import logger
from lib.utils import DockerNetwork, DockerService

class LTEUE(DockerService):

    def __init__(self,
            name: str,
            client: docker.APIClient,
            config: dict,
    ):

        self.name = name
        self.client = client

        self.container = client.create_container(
            #image='rdefosseoai/oai-lte-ue:develop',
            image='oai-lte-ue:latest',
            name=name,
            hostname='ubuntu',
            #volumes=['/opt/oai-lte-ue/ue_usim.conf','/opt/oai-lte-ue/entrypoint.sh'],
            host_config=client.create_host_config(
                network_mode='host',
                privileged=True,
                #binds=[
                #    '{0}:/opt/oai-lte-ue/ue_usim.conf'.format(conf_file),
                #    '{0}:/opt/oai-lte-ue/entrypoint.sh'.format(entry_file),
                #],
            ),
            environment=config,
            entrypoint='/usr/bin/env',
            #command="/bin/bash -c  \" ./bin/uhd_images_downloader.py -t b2xx_b210_fpga_default && ./bin/uhd_images_downloader.py -t b2xx_common_fw_default && ./bin/usim -g -c /opt/oai-lte-ue/ue_usim.conf && ./bin/nvram -g -c /opt/oai-lte-ue/ue_usim.conf  && exec /opt/oai-lte-ue/bin/lte-uesoftmodem.Rel15 -C 2680000000 -r 25 --ue-rxgain 120 --ue-txgain 0 --ue-max-power 0 --ue-scan-carrier --nokrnmod 1; \" "
            command="/bin/bash -c  \" chmod +x /opt/oai-lte-ue/entrypoint.sh && /opt/oai-lte-ue/entrypoint.sh  && ./bin/uhd_images_downloader.py -t b2xx_b210_fpga_default && ./bin/uhd_images_downloader.py -t b2xx_common_fw_default && ./bin/usim -g -c /opt/oai-lte-ue/ue_usim.conf && ./bin/nvram -g -c /opt/oai-lte-ue/ue_usim.conf  && exec /opt/oai-lte-ue/bin/lte-uesoftmodem.Rel15 -C {0}000000 -r {1} --ue-rxgain {2} --ue-txgain {3} --ue-max-power {4} --ue-scan-carrier --nokrnmod 1; \" ".format(config['DL_FREQUENCY_IN_MHZ'],config['NB_PRB'],config['RX_GAIN'],config['TX_GAIN'],config['MAX_POWER'])
        )

        # start the container
        client.start(self.container)
        logger.info('{0} service successfully started at {1}.'.format(self.name,self.client.base_url))
        
        #dkg = client.attach(container, stdout=True, stderr=True, stream=True, logs=True, demux=False)
        #for line in dkg:
        #    line = line.decode().rstrip()
        #    print(line)

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
    
    input("Press any key to continue...")

    lteue.__del__()

