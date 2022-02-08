import docker
import time
from loguru import logger

def enbipcheck(client, public_network, self_public_ip,mme_public_ip,spgwc_public_ip):

    networking_config = client.create_networking_config({
        public_network['name']: client.create_endpoint_config(
            ipv4_address=self_public_ip,
        ),
    })

    container = client.create_container(
        image='rdefosseoai/oai-enb:develop',
        name='check-enb-connections',
        hostname='ubuntu',
        host_config=client.create_host_config(privileged=True),
        networking_config=networking_config,
        entrypoint='/usr/bin/env',
        command= "/bin/bash -c  \"ping -c 3 {0} && ping -c 3 {1};\" ".format(mme_public_ip,spgwc_public_ip),
    )
    
    logger.info('Checking eNodeB connection to SPGWC and MME services...')

    # start the container
    client.start(container)

    dkg = client.attach(container, stdout=True, stderr=True, stream=True, logs=True, demux=False)
    for line in dkg:
        line = line.decode().rstrip()
        print(line)
        if "Unreachable" in line:
            logger.error("Cannot reach SPGWC or MME from eNodeB.")
            raise Exception("Cannot reach SPGWC or MME from eNodeB.")

    return container

def enb(client, public_network, self_public_ip, mme_public_ip, conf_file, entry_file):

    networking_config = client.create_networking_config({
        public_network['name']: client.create_endpoint_config(
            ipv4_address=self_public_ip,
        ),
    })

    container = client.create_container(
        image='rdefosseoai/oai-enb:develop',
        name='prod-oai-enb',
        hostname='ubuntu',
        volumes=['/opt/oai-enb/enb.conf','/opt/oai-enb/entrypoint.sh'],
        host_config=client.create_host_config(
            privileged=True,
            binds=[
                '{0}:/opt/oai-enb/enb.conf'.format(conf_file),
                '{0}:/opt/oai-enb/entrypoint.sh'.format(entry_file),
            ],
        ),
        networking_config=networking_config,
        environment={
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
            'ENB_X2_IP_ADDRESS':self_public_ip,
            'ENB_S1C_IF_NAME':'eth0',
            'ENB_S1C_IP_ADDRESS':self_public_ip,
            'ENB_S1U_IF_NAME':'eth0',
            'ENB_S1U_IP_ADDRESS':self_public_ip,
            'THREAD_PARALLEL_CONFIG':'PARALLEL_SINGLE_THREAD',
            'FLEXRAN_ENABLED':'no',
            'FLEXRAN_INTERFACE_NAME':'eth0',
            'FLEXRAN_IPV4_ADDRESS':'CI_FLEXRAN_CTL_IP_ADDR',
        },
        #entrypoint='/usr/bin/env',
        #command="/bin/bash -c  \" ./bin/uhd_images_downloader.py -t b2xx_b210_fpga_default && ./bin/uhd_images_downloader.py -t b2xx_common_fw_default && exec /opt/oai-enb/bin/lte-softmodem.Rel15 -O /opt/oai-enb/enb.conf; \" "
        #command="/bin/bash -c  \" chmod +x /opt/oai-enb/entrypoint.sh && /opt/oai-enb/entrypoint.sh  && ./bin/uhd_images_downloader.py -t b2xx_b210_fpga_default && ./bin/uhd_images_downloader.py -t b2xx_common_fw_default && exec /opt/oai-enb/bin/lte-softmodem.Rel15 -O /opt/oai-enb/enb.conf; \" "
    )

    # start the container
    client.start(container)
    
    logger.info('EnodeB successfully started at {0} with ip {1}'.format(public_network['name'],self_public_ip))

    #dkg = client.attach(container, stdout=True, stderr=True, stream=True, logs=True, demux=False)
    #for line in dkg:
    #    line = line.decode().rstrip()
    #    print(line)

    return container

if __name__ == "__main__":

    # connect to the EPC host dockerhub
    #client = DockerClient(base_url='192.168.2.2:2375');
    #client = docker.APIClient(base_url='192.168.2.2:2375')
    docker_host_name = 'finarfin'
    docker_port = '2375'
    public_network_dict = { 'name':'prod-oai-public-net', 'subnet':'192.168.61.192/26' }
    new_network = False

    logger.info('Starting LTE eNodeB on {0} port {1}.'.format(docker_host_name,docker_port))
    client = docker.APIClient(base_url=docker_host_name+':'+docker_port)

    if new_network:
        # create prod-oai-public-net
        ipam_pool_public = docker.types.IPAMPool(
            subnet=public_network_dict['subnet'],
        )
        ipam_config_public = docker.types.IPAMConfig(
            pool_configs=[ipam_pool_public]
        )
        public_network = client.create_network(public_network_dict['name'],ipam=ipam_config_public)
    else:
        # find prod-oai-public-net
        found_nets = client.networks(names=[public_network_dict['name']])
        if len(found_nets) == 0:
            logger.error('Could not find network {0} in docker.'.format(public_network_dict['name']))
            raise Exception('Could not find network {0} in docker.'.format(public_network_dict['name']))
        else:
            public_network = found_nets[0]

    # create and run enbipcheck container
    mme_public_ip = '192.168.61.195'
    spgwc_public_ip = '192.168.61.196'
    enb_public_ip = '192.168.61.198'
    enbipcheck_container = enbipcheck(client,public_network_dict,enb_public_ip,mme_public_ip,spgwc_public_ip)

    try:
        client.kill(enbipcheck_container)
    except:
        pass

    try:
        client.remove_container(enbipcheck_container)
    except:
        pass

    logger.warning('ENodeB connection check container tore down and removed.')

    
    # create and run enb container
    #conf_file = "/home/wlab/oai-all-in-docker/enodeb/enb.conf"
    conf_file = "/home/wlab/oai-all-in-docker/enodeb/generic.conf"
    entry_file = "/home/wlab/oai-all-in-docker/enodeb/entrypoint.sh"
    enb_container = enb(client,public_network_dict,enb_public_ip, mme_public_ip, conf_file, entry_file)


    input("Press any key to continue...")

    try:
        client.kill(enb_container)
    except:
        pass

    try:
        client.remove_container(enb_container)
    except:
        pass

    if new_network:
        try:
            client.remove_network(public_network['Id'])
        except:
            pass

