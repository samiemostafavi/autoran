# OAI repositories

RAN repo: https://gitlab.eurecom.fr/oai/openairinterface5g

Core network repo: https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-fed

Docker images: https://hub.docker.com/u/rdefosseoai

# oai-ran-docker

# LTE EnB

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

in the container:

    ./bin/uhd_images_downloader.py
    /opt/oai-lte-ue/bin/lte-uesoftmodem.Rel15 -C 2680000000 -r 25 --ue-rxgain 120 --ue-txgain 0 --ue-max-power 0 --ue-scan-carrier --nokrnmod 1 --noS1
    
    
