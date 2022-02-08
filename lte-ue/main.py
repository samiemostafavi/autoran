import docker
import time
from loguru import logger

def ue(client, conf_file, entry_file):

    container = client.create_container(
        image='rdefosseoai/oai-lte-ue:develop',
        name='prod-oai-lte-ue',
        hostname='ubuntu',
        volumes=['/opt/oai-lte-ue/ue_usim.conf','/opt/oai-lte-ue/entrypoint.sh'],
        host_config=client.create_host_config(
            network_mode='host',
            privileged=True,
            binds=[
                '{0}:/opt/oai-lte-ue/ue_usim.conf'.format(conf_file),
                '{0}:/opt/oai-lte-ue/entrypoint.sh'.format(entry_file),
            ],
        ),
        environment={
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
        },
        entrypoint='/usr/bin/env',
        command="/bin/bash -c  \" ./bin/uhd_images_downloader.py -t b2xx_b210_fpga_default && ./bin/uhd_images_downloader.py -t b2xx_common_fw_default && ./bin/usim -g -c /opt/oai-lte-ue/ue_usim.conf && ./bin/nvram -g -c /opt/oai-lte-ue/ue_usim.conf  && exec /opt/oai-lte-ue/bin/lte-uesoftmodem.Rel15 -C 2680000000 -r 25 --ue-rxgain 120 --ue-txgain 0 --ue-max-power 0 --ue-scan-carrier --nokrnmod 1; \" "
        #command="/bin/bash -c  \" chmod +x /opt/oai-lte-ue/entrypoint.sh && /opt/oai-lte-ue/entrypoint.sh  && ./bin/uhd_images_downloader.py -t b2xx_b210_fpga_default && ./bin/uhd_images_downloader.py -t b2xx_common_fw_default && ./bin/usim -g -c /opt/oai-lte-ue/ue_usim.conf && ./bin/nvram -g -c /opt/oai-lte-ue/ue_usim.conf  && exec /opt/oai-lte-ue/bin/lte-uesoftmodem.Rel15 -C 2680000000 -r 25 --ue-rxgain 120 --ue-txgain 0 --ue-max-power 0 --ue-scan-carrier --nokrnmod 1; \" "
    )

    # start the container
    client.start(container)
    

    #dkg = client.attach(container, stdout=True, stderr=True, stream=True, logs=True, demux=False)
    #for line in dkg:
    #    line = line.decode().rstrip()
    #    print(line)

    return container

if __name__ == "__main__":

    # connect to the EPC host dockerhub
    #client = DockerClient(base_url='192.168.2.2:2375');
    #client = docker.APIClient(base_url='192.168.2.2:2375')
    docker_host_name = 'fingolfin'
    docker_port = '2375'

    logger.info('Starting LTE UE on {0} port {1}.'.format(docker_host_name,docker_port))
    client = docker.APIClient(base_url=docker_host_name+':'+docker_port)

    # create and run ue container
    conf_file = "/home/wlab/oai-all-in-docker/lte-ue/ue_usim.conf"
    #conf_file = "/home/wlab/oai-all-in-docker/lte-ue/ue_generic.conf"
    entry_file = "/home/wlab/oai-all-in-docker/lte-ue/entrypoint.sh"
    ue_container = ue(client, conf_file, entry_file)
    
    logger.info('UE successfully started at {0}.'.format(docker_host_name))
    
    input("Press any key to continue...")

    try:
        client.kill(ue_container)
    except:
        pass

    try:
        client.remove_container(ue_container)
    except:
        pass


