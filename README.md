# OAI repositories

### RAN

LTE & 5G Radio Access Network (RAN) repository: https://gitlab.eurecom.fr/oai/openairinterface5g

### Core Networks

5G Core Network (CN) repository: https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-fed

LTE Eovlved Packet Core (EPC) repository: https://github.com/OPENAIRINTERFACE/openair-epc-fed.

### Docker Images

Docker images: https://hub.docker.com/u/rdefosseoai

# Setup Schematic

![Setup Schematic](https://github.com/samiemostafavi/oai-lte-docker/blob/main/OAICN-Network-Deployment-Explanation.png "Setup Schematic")


# Step 1. Start LTE Evolved Packet Core (EPC)

Openairinterface LTE EPC consists of:
- HSS
- MME
- SPGW-U+SPGW-C

The federation repository is located at https://github.com/OPENAIRINTERFACE/openair-epc-fed.

There is 2 options regarding deployment of MME in Openairinterface:
- Magma MME [Start here](https://github.com/OPENAIRINTERFACE/openair-epc-fed/blob/master/docs/DEPLOY_HOME_MAGMA_MME.md)
- Legacy MME [Start here](https://github.com/OPENAIRINTERFACE/openair-epc-fed/blob/master/docs/DEPLOY_HOME.md) *

*Currently, OAI UE does not connect to Magma MME. Hence, in this tutorial we use `Legacy MME` which is not stable and could need restart after a few hours.

You can configure the EPC by modifiying the docker-compose file located at

    openair-epc-fed/docker-compose/oai-mme-legacy/docker-compose.yml

1. Init database

        cd openair-epc-fed/docker-compose/oai-mme-legacy/
        docker-compose up -d db_init
        docker logs prod-db-init --follow

2. After getting init *ok*, Deploy
        
        docker rm -f prod-db-init
        docker-compose up -d oai_spgwu

    Check if the containers are up or logs
    
        docker ps -a
        docker logs prod-oai-hss
        
    Check the deployed containers networks and ip of each service
    
        docker network ls
        docker network inspect prod-oai-public-net
    
3. Undeploy

        docker-compose down
    

# Step 2. Start LTE EnB

We use USRP B210 as the software-defined radio in this tutorial. There is a config file located at 

    https://gitlab.eurecom.fr/oai/openairinterface5g/-/blob/develop/ci-scripts/conf_files/enb.band7.tm1.fr1.25PRB.usrpb210.conf
    
which is copied to `enodeb/enb.conf` and modified as the steps below

- Modify `plmn_list` which consists of MCC, MNC, and TAC (`tracking_area_code`) so it matches MME configuration.
- Modify `mme_ip_address.ipv4` so it matches MME configuration: "CI_MME_IP_ADDR"
- Modify `NETWORK_INTERFACES` section and set an arbitrary ip address for enb server in the `prod-oai-public-net` subnet: "CI_ENB_IP_ADDR". NOTE: if you are runing enb on the same machine, `ENB_INTERFACE_NAME_FOR_*` is not important. Otherwise, set it properly.


## Using docker-compose

To start:

    cd enodeb
    docker pull rdefosseoai/oai-enb:develop
    docker-compose -f docker-compose.yaml up

Then remove the container:

    docker stop /oaienb 
    docker rm /oaienb

## Using Docker CLI

on the host:

    docker pull rdefosseoai/oai-enb:develop
    
check USRP is connected:
    
    uhd_find_devices

Run the container in host and privileged mode:
    
    docker run -it --net=host --privileged rdefosseoai/oai-enb:2021.w46 /bin/bash

on the host, find the running container name:

    docker container ls

copy the enb conf file to the container:
    
    docker cp openairinterface5g/ci-scripts/conf_files/enb.band7.tm1.25PRB.usrpb210.conf $CONTAINER_NAME$:/opt/oai-enb

in the container:

    ./bin/uhd_images_downloader.py
    /opt/oai-enb/bin/lte-softmodem.Rel15 -O enb.band7.tm1.25PRB.usrpb210.conf --nokrnmod 1 --noS1 --eNBs.[0].rrc_inactivity_threshold 0

# LTE UE

## Configuration

    https://gitlab.eurecom.fr/oai/openairinterface5g/-/wikis/how-to-run-oaisim-with-multiple-ue
    https://gitlab.eurecom.fr/oai/openairinterface5g/-/blob/develop/doc/BASIC_SIM.md
    https://gitlab.eurecom.fr/oai/openairinterface5g/-/blob/develop/openair3/NAS/TOOLS/ue_sim_ci.conf
    https://gitlab.eurecom.fr/oai/openairinterface5g/-/wikis/l2-nfapi-simulator/l2-nfapi-simulator-w-S1-same-machine#3-retrieve-the-oai-enb-ue-source-code

Good explanation about UE sim config:

    https://github.com/danielgora/openair-epc-fed/blob/develop/docs/EPC_IN_A_BOX.md
    
An important point from mailing list with the name `UE-softmodem fails to add ip address`:

I would say `nasmesh` is not much more worked on
here at Eurecom. So use `--nokrnmod 1` all the time.

## Using docker-compose

To start:

    cd lte-ue
    docker pull rdefosseoai/oai-lte-ue:develop
    docker-compose -f docker-compose.yaml up

Then remove the container:

    docker stop /oaiue
    docker rm /oaiue

## Using Docker CLI

on the host:

    docker pull rdefosseoai/oai-lte-ue:develop

run the container and override entrypoint:

    docker run -it --net=host --privileged --entrypoint /bin/bash rdefosseoai/oai-lte-ue:develop
    
    docker run -it --net=host --privileged --entrypoint /bin/bash --mount type=bind,source=/home/wlab/oai-ran-docker/lte-ue,target=/app rdefosseoai/oai-lte-ue:develop

in the container:

    ./bin/uhd_images_downloader.py
    
    ./bin/usim -g -c /app/ue_usim.conf
    
    /opt/oai-lte-ue/bin/lte-uesoftmodem.Rel15 -C 2680000000 -r 25 --ue-rxgain 120 --ue-txgain 0 --ue-max-power 0 --ue-scan-carrier --nokrnmod 1 --noS1
    
    ./bin/lte-uesoftmodem.Rel15 -C 2680000000 -r 25 --ue-rxgain 120 --ue-txgain 0 --ue-max-power 0 --ue-scan-carrier
    
    

