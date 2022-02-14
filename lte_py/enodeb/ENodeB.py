from ipaddress import IPv4Interface, IPv4Network, IPv4Address
import docker
import time
from loguru import logger
from lte_py.utils import DockerNetwork, DockerService

class ENodeB(DockerService):
    def __init__(self,
        name: str,
        client: docker.APIClient,
        ip: IPv4Address,
        network: DockerNetwork,
        config: dict,
    ):

        self.client = client
        self.name = name
        self.ip = ip
        self.network = network

        # First, check if enb can reach SPGWC and MME
        networking_config = client.create_networking_config({
            network.name: client.create_endpoint_config(
                ipv4_address=str(ip),
            ),
        })

        conn_check_container = client.create_container(
            #image='rdefosseoai/oai-enb:develop',
            image='oai-enb:latest',
            name='check-enb-connections',
            hostname='ubuntu',
            host_config=client.create_host_config(privileged=True),
            networking_config=networking_config,
            entrypoint='/usr/bin/env',
            command= "/bin/bash -c  \"ping -c 3 {0} && ping -c 3 {1};\" ".format(config['mme_ip'],config['spgwc_ip']),
        )
        
        logger.info('Checking eNodeB connection to SPGWC and MME services...')

        # start the container
        client.start(conn_check_container)

        dkg = client.attach(conn_check_container, stdout=True, stderr=True, stream=True, logs=True, demux=False)
        for line in dkg:
            line = line.decode().rstrip().partition('\n')[0]
            #print(line)
            if "Unreachable" in line:
                logger.error("Cannot reach SPGWC or MME from eNodeB.")
                raise Exception("Cannot reach SPGWC or MME from eNodeB.")

            if "icmp_seq=" in line:
                logger.info(line)

        try:
            client.kill(conn_check_container)
        except:
            pass

        try:
            client.remove_container(conn_check_container)
        except:
            pass

        logger.warning('ENodeB connection check container tore down and removed.')


        # now start the real enodeB container
        networking_config = client.create_networking_config({
            network.name: client.create_endpoint_config(
                ipv4_address=str(ip),
            ),
        })

        self.container = client.create_container(
            image='oai-enb:latest',
            name=name,
            hostname='ubuntu',
            host_config=client.create_host_config(
                privileged=True,
            ),
            networking_config=networking_config,
            environment=config,
            entrypoint='/usr/bin/env',
            #command="/bin/bash -c  \" ./bin/uhd_images_downloader.py -t b2xx_b210_fpga_default && ./bin/uhd_images_downloader.py -t b2xx_common_fw_default && exec /opt/oai-enb/bin/lte-softmodem.Rel15 -O /opt/oai-enb/enb.conf; \" "
            command="/bin/bash -c  \" chmod +x /opt/oai-enb/entrypoint.sh && /opt/oai-enb/entrypoint.sh  && ./bin/uhd_images_downloader.py -t b2xx_b210_fpga_default && ./bin/uhd_images_downloader.py -t b2xx_common_fw_default && exec /opt/oai-enb/bin/lte-softmodem.Rel15 -O /opt/oai-enb/enb.conf; \" "
        )

        # start the container
        client.start(self.container)
        logger.info('{0} service successfully started at {1} with ip {2}.'.format(self.name,self.client.base_url,ip))

if __name__ == "__main__":

    # connect to the EPC host dockerhub
    docker_host_name = 'finarfin'
    docker_port = '2375'
    logger.info('Starting LTE eNodeB on {0} port {1}.'.format(docker_host_name,docker_port))
    client = docker.APIClient(base_url=docker_host_name+':'+docker_port)
   
    # creating or fetching network
    public_network = DockerNetwork(client,IPv4Network('192.168.61.192/26'),'prod-oai-public-net')

    # create and run enbipcheck container
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
    
