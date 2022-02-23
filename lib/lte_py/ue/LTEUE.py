import docker
import time
from loguru import logger
from lib.utils import DockerNetwork, DockerService
from ipaddress import IPv4Interface, IPv4Network, IPv4Address 
import re
import json
from .LTEUERouter import UERouter
from lib.utils.command_runner import RemoteRunner

def is_json(myjson):
    try:
        json.loads(myjson)
    except ValueError as e:
        return False
    return True

class LTEUE(DockerService):
    assigned_ip: IPv4Interface

    def __init__(self,
            name: str,
            client: docker.APIClient,
            config: dict,
            routing_config: dict,
    ):
        self.assigned_ip = None
        self.name = name
        self.client = client
        self.routing_config = routing_config

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
            healthcheck=docker.types.Healthcheck(
                test="/bin/bash -c \" ping -c1 12.1.1.1 &>/dev/null; \"",
                interval=1*1000000000,
                timeout=1*1000000000,
                retries=0,
            ),
            environment=config,
            entrypoint='/usr/bin/env',
            #command="/bin/bash -c  \" ./bin/uhd_images_downloader.py -t b2xx_b210_fpga_default && ./bin/uhd_images_downloader.py -t b2xx_common_fw_default && ./bin/usim -g -c /opt/oai-lte-ue/ue_usim.conf && ./bin/nvram -g -c /opt/oai-lte-ue/ue_usim.conf  && exec /opt/oai-lte-ue/bin/lte-uesoftmodem.Rel15 -C 2680000000 -r 25 --ue-rxgain 120 --ue-txgain 0 --ue-max-power 0 --ue-scan-carrier --nokrnmod 1; \" "
            command="/bin/bash -c  \" chmod +x /opt/oai-lte-ue/entrypoint.sh && " +
                                      " /opt/oai-lte-ue/entrypoint.sh  && " +
                                      " ./bin/uhd_images_downloader.py -t b2xx_b210_fpga_default && " +
                                      " ./bin/uhd_images_downloader.py -t b2xx_common_fw_default && " +
                                      " ./bin/usim -g -c /opt/oai-lte-ue/ue_usim.conf && " +
                                      " ./bin/nvram -g -c /opt/oai-lte-ue/ue_usim.conf && " +
                                      " exec /opt/oai-lte-ue/bin/lte-uesoftmodem.Rel15 " +
                                      " -C {0}000000 ".format(config['DL_FREQUENCY_IN_MHZ']) +
                                      " -r {0} ".format(config['NB_PRB']) + 
                                      " --ue-rxgain {0} ".format(config['RX_GAIN']) +
                                      " --ue-txgain {0} ".format(config['TX_GAIN']) +
                                      " --ue-max-power {0} ".format(config['MAX_POWER']) +
                                      " --ue-scan-carrier --nokrnmod 1; \" "
        )

        # start the container
        client.start(self.container)
        logger.info('{0} service successfully started at {1}.'.format(self.name,self.client.base_url))
        
        
        manager_container = client.create_container(
            image='oai-lte-ue:latest',
            name='prod-lte-ue-manager',
            hostname='ubuntu',
            host_config=client.create_host_config(
                network_mode='host',
                privileged=True,
                restart_policy={
                    'Name':'always',
                },
            ),
            entrypoint="/bin/bash -c \"sleep 1 && ip -j --brief address show oaitun_ue1 \" ",
        )
        
        # start the container
        client.start(manager_container)
        logger.info('Waiting for UE at {0} to connect...'.format(self.name,self.client.base_url))
        
        succeeded = False
        complete_logs = ''
        for i in range(0,30):
            time.sleep(1)
            new_complete_logs = client.logs(manager_container,stdout=True, stderr=True, tail='all').decode()
            logs = new_complete_logs.replace(complete_logs,'',1)
            complete_logs = new_complete_logs

            if logs:              
                #print(logs)
                if is_json(logs):
                    try:
                        js_dict = json.loads(logs)
                        js_dict = list(filter(None, js_dict))
                        res_ip = js_dict[0]['addr_info'][0]['local']
                        res_preflen = js_dict[0]['addr_info'][0]['prefixlen']
                        succeeded = True
                    except:
                        pass

            if succeeded:
                break

        if not succeeded:
            logger.error("UE connection timeout.")

            try:
                client.kill(manager_container)
            except:
                pass

            try:
                client.remove_container(manager_container)
            except:
                pass

            logger.warning('UE connection checker container tore down and removed.')

            raise Exception("UE connection timeout.")

        try:
            client.kill(manager_container)
        except:
            pass

        try:
            client.remove_container(manager_container)
        except:
            pass

        logger.warning('UE connection checker container tore down and removed.')
    
        self.assigned_ip = IPv4Interface(str(res_ip)+'/'+str(res_preflen))

        logger.info('UE at {0} is attached and connected with ip {1}.'.format(self.client.base_url,self.assigned_ip))

        self.rr = RemoteRunner(
            client=self.client,
            name='prod-remoterunner',
        )

        # initiate CoreRouter
        self.ue_router = UERouter(
            client=self.client,
            docker_public_network='192.168.61.192/26',
            epc_main_lte_ip='12.1.1.1',
            epc_bridge_ip='192.168.61.193',
            lte_assigned_ip=str(self.assigned_ip.ip),
            remote_runner=self.rr,
            routing_config=self.routing_config,
        )


        logger.info("Waiting for UE at {0} to handshake over the tunnel with EPC...".format(self.client.base_url))
        tunnel_handshake = self.ue_router.wait_for_tunnel(
            tunnel_epc_ip=str(self.routing_config['epc_tun_if'].ip),
        )
        if not tunnel_handshake:
            logger.error("UE at {0} could not handshake over the tunnel with EPC.".format(self.client.base_url))
        else:
            logger.info("UE at {0} successfully tested gre tunnel with EPC.".format(self.client.base_url))
            
            # Expose UE external network
            self.ue_router.create_tunnel_route(
                target_net=str(self.routing_config['epc_ex_net']),
                epc_tunnel_ip=str(self.routing_config['epc_tun_if'].ip),
            )

            logger.info("UE at {0} successfully added a route from {1} to EPC external network {2}.".format(self.client.base_url,'tun0',str(self.routing_config['epc_ex_net'])))
        
            self.ue_router.enable_iptables_forwarding()


    def is_connected(self) -> bool:

        result = self.client.inspect_container(self.name)['State']['Health']['Status']
        if result == 'healthy':
            return True
        else:
            return False

    def __del__(self):
        try:
            self.ue_router
        except:
            pass
        else:
            self.ue_router.__del__()

        super().__del__()


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

