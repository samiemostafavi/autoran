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


## Deploy UE Using Docker CLI

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
    
