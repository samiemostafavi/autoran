#!/bin/bash

./bin/uhd_images_downloader.py
/opt/oai-enb/bin/lte-softmodem.Rel15 -O /opt/oai-enb/enb.conf --nokrnmod 1 --noS1 --eNBs.[0].rrc_inactivity_threshold 0
