# OAI All-in-Docker

In this repository I provide the missing docker-compose files, configurations, and explanations required for running an end-to-end Openairinterface (OAI) LTE or 5G standalone network. Therefore, we use software-defined radios only and all user equipment (UE) instances are OAI-based e.g. `lte-ue` or `nr-ue`.

- [How to start an End-to-End SDR-based LTE network using OAI](docs/LTE.md)
- [How to start an End-to-End SDR-based standalone 5G network using OAI](docs/5G_SA_MINI_NRF.md)
- [How to start an End-to-End SDR-based non-standalone 5G network using OAI](docs/5G_NSA.md)

# OAI repositories

### RAN

LTE & 5G Radio Access Network (RAN) repository: https://gitlab.eurecom.fr/oai/openairinterface5g

### Core Networks

5G Core Network (CN) repository: https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-fed

LTE Eovlved Packet Core (EPC) repository: https://github.com/OPENAIRINTERFACE/openair-epc-fed.

### Docker Images

Docker images: https://hub.docker.com/u/rdefosseoai

# OAI Python API

This section is related to a Python library provided in this repository which is called `oai-py`. Instead of running the docker commands manually on the radio hosts, you can write a Python script from anywhere accessible through the network and run the radio access network or the core network.

- [How to start an End-to-End SDR-based LTE network using OAI-py](docs/LTE-oaipy.md)
