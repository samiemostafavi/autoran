## Deploy eNodeB Using Docker CLI

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
