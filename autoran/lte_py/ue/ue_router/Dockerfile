# running interactive session:
### docker run --network host  -it prod_ue_router /bin/bash
# running in the background:
### docker run --network host prod_ue_router
# build the image:
### docker build -t ue_router .

#Download base image ubuntu 20.04
FROM ubuntu:20.04

# LABEL about the custom image
LABEL maintainer="ssmos@kth.se"
LABEL version="0.1"
LABEL description="UE Router"

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

RUN mkdir -p /home/host

#COPY wlan-exp_v1.9.0.zip /home/
#RUN unzip /home/wlan-exp_v1.9.0.zip -d /home/
#COPY nodes_config.ini /home/wlan-exp_v1.9.0/
#COPY init_nodes.py /home/wlan-exp_v1.9.0/

# Expose Port for the Application 
#WORKDIR "/home/wlan-exp_v1.9.0/"
WORKDIR "/home/host"
CMD python3.6 main.py
