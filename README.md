# OAI repositories

### RAN

LTE & 5G Radio Access Network (RAN) repository: https://gitlab.eurecom.fr/oai/openairinterface5g

### Core Networks

5G Core Network (CN) repository: https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-fed

LTE Eovlved Packet Core (EPC) repository: https://github.com/OPENAIRINTERFACE/openair-epc-fed.

### Docker Images

Docker images: https://hub.docker.com/u/rdefosseoai

# Setup Schematic

![alt text](network.png "Title")


# Step 1. Starting LTE Evolved Packet Core (EPC)

Openairinterface LTE EPC consists of:
1. HSS
2. MME
3. SPGW-U+SPGW-C

The federation repository is located at https://github.com/OPENAIRINTERFACE/openair-epc-fed.

There is 2 options regarding deployment of MME in Openairinterface:
- Magma MME [Start here](https://github.com/OPENAIRINTERFACE/openair-epc-fed/blob/master/docs/DEPLOY_HOME_MAGMA_MME.md)
- Legacy MME [Start here](https://github.com/OPENAIRINTERFACE/openair-epc-fed/blob/master/docs/DEPLOY_HOME.md) *

*Currently, OAI UE does not connect to Magma MME. Hence, in this tutorial we use `Legacy MME` which is not stable and could need restart after a few hours.

# LTE EnB

## Configure

    https://gitlab.eurecom.fr/oai/openairinterface5g/-/blob/develop/ci-scripts/conf_files/enb.band7.tm1.fr1.25PRB.usrpb210.conf

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
    
    

