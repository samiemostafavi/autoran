from ipaddress import IPv4Interface, IPv4Network, IPv4Address
import docker
from loguru import logger
import time
from threading import Thread, Lock

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

class RemoteRunner():
    def __init__(self,
            client: docker.APIClient,
            name: str,
    ):
        self.client = client
        self.name = name
        self.mutex = Lock()
        self.time_res = 0.1

    def run_command(self,
            command: str,
            timeout: int = 2,
        ):
        
        self.mutex.acquire()

        command_container = self.client.create_container(
            image='router_admin:latest',
            name=self.name,
            hostname='ubuntu',
            host_config=self.client.create_host_config(
                network_mode='host',
                privileged=True,
            ),
            entrypoint='/usr/bin/env',
            command="/bin/bash -c  \" " + command + " && echo 'OK' \" "
        )

        # start the container
        self.client.start(command_container)

        success = False
        r = int(timeout/self.time_res)
        for i in range(1,r):
            time.sleep(self.time_res)
            logs = self.client.logs(command_container,stdout=True, stderr=True, tail='all')
            logs = logs.decode().rstrip()
            #print(logs)
            if "OK" in logs:
                success = True
                break
        if not success:
            logger.error('Running the command: \" ' + command + " \" did not work on {0}".format(self.client.base_url))
            terminate_container(self.client,command_container)
            self.mutex.release()
            return False
            #raise Exception('Running the routing command: \" ' + command + " \" did not work on {0}".format(client.base_url))

        terminate_container(self.client,command_container)
        self.mutex.release()
        return True


