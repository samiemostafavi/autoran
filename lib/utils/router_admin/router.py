from ipaddress import IPv4Interface, IPv4Network, IPv4Address
import docker
from loguru import logger
import time


def terminate_container(
        client,
        container,
    ):

    try:
        client.kill(container)
    except:
        pass

    try:
        client.remove_container(container)
    except:
        pass
    

def run_command(
        client: docker.APIClient, 
        command: str
    ):
    command_container = client.create_container(
        image='router_admin:latest',
        name='prod_router',
        hostname='ubuntu',
        host_config=client.create_host_config(
            network_mode='host',
            privileged=True,
        ),
        entrypoint='/usr/bin/env',
        command="/bin/bash -c  \" " + command + " && echo 'OK' \" "
    )

    # start the container
    client.start(command_container)

    success = False
    for i in range(1,20):
        time.sleep(0.1)
        logs = client.logs(command_container,stdout=True, stderr=True, tail='all')
        logs = logs.decode().rstrip()
        #print(logs)
        if "OK" in logs:
            success = True
            break
    if not success:
        logger.error('Running the routing command: \" ' + command + " \" did not work on {0}".format(client.base_url))
        terminate_container(client,command_container)
        raise Exception('Running the routing command: \" ' + command + " \" did not work on {0}".format(client.base_url))

    terminate_container(client,command_container)




