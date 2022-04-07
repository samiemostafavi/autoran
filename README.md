# AutoRAN: Automatic remote deployment of open-source radio access networks

Use this Python package to start an end-to-end open-source radio network on remote machines with software-defined radios. You will be able to observe and control the network, e.g. when a UE attaches. Under the hood, we use Radio network Docker images provided by openairinterface, srs, o-ran, and etc.


    pip install git+https://github.com/samiemostafavi/autoran.git


# OAI All-in-Docker

In this section, I provide the missing docker-compose files, configurations, and explanations required for running an end-to-end Openairinterface (OAI) LTE or 5G standalone network. Therefore, we use software-defined radios only and all user equipment (UE) instances are OAI-based e.g. `lte-ue` or `nr-ue`.

- [How to start an End-to-End SDR-based LTE network using OAI](docs/LTE.md)
- [How to start an End-to-End SDR-based standalone 5G network using OAI](docs/5G_SA_MINI_NRF.md)

# OAI repositories

### RAN

LTE & 5G Radio Access Network (RAN) repository: https://gitlab.eurecom.fr/oai/openairinterface5g

### Core Networks

5G Core Network (CN) repository: https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-fed

LTE Eovlved Packet Core (EPC) repository: https://github.com/OPENAIRINTERFACE/openair-epc-fed.

### Docker Images

Docker images: https://hub.docker.com/u/rdefosseoai

# OAI Python API

This section is related to a Python library provided in this repository which is called `oai-py`. Instead of running the docker commands manually on the radio hosts, you can use this library and run a Python script from anywhere accessible through the network and run the radio access network or the core network remotely and automatic. We use `docker-py` as the main tool to interact with the radio and packet core hosts.

- [How to start an End-to-End SDR-based LTE network using OAI-py](docs/LTE-oaipy.md)
