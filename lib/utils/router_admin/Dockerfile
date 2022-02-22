# running interactive session:
### docker run --privileged --network host -it epc_router /bin/bash
# running in the background:
### docker run --privileged --network host epc_router
# build the image:
### docker build --network=host -t epc_router .

#Download base image ubuntu 20.04
FROM ubuntu:20.04

# LABEL about the custom image
LABEL maintainer="ssmos@kth.se"
LABEL version="0.1"
LABEL description="EPC Router"

# Disable Prompt During Packages Installation
ARG DEBIAN_FRONTEND=noninteractive

# Update Ubuntu Software repository
RUN apt-get -y update

RUN apt-get install software-properties-common -y

RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update
RUN apt-get install python3.6 -y
RUN apt-get install unzip -y
RUN apt-get install net-tools -y
RUN apt-get install -y iputils-ping
RUN apt-get install -y iproute2
