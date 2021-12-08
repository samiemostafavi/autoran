# EPC side:

## Goal 1: Ping EPC host from UE host

Configure the routing so you can ping `enp5s0` on `finarfin` with an arbitrary ip in the subnet `10.0.0.0/24`.

1. First, assign the ip address on `finarfin`:
	
		sudo ip addr add 10.0.0.5/24 dev enp5s0

2. By running this on EPC host, I could ping UEs from EPC host. So we know that the ping response can go back:

		$ sudo ip route add 12.1.1.0/24 via 192.168.61.197
		$ ip route show
		12.1.1.0/24 via 192.168.61.197 dev br-68cb1f58ee58
		$ ping 12.1.1.2
		PING 12.1.1.2 (12.1.1.2) 56(84) bytes of data.
		64 bytes from 12.1.1.2: icmp_seq=1 ttl=63 time=21.1 ms
		64 bytes from 12.1.1.2: icmp_seq=2 ttl=63 time=27.9 ms

	`192.168.61.197` and `12.1.1.1` are interface ips within `oai_spgwu` which is the LTE network gateway.

3. By running this on UE host, I could ping `enp5s0` from UE host:

		$ sudo ip route add 10.0.0.0/24 via 12.1.1.1 dev oaitun_ue1
		$ ip route show
		...
		10.0.0.0/24 via 12.1.1.1 dev oaitun_ue1
		...
		$ ping 192.168.61.197
		PING 192.168.61.197 (192.168.61.197) 56(84) bytes of data.
		64 bytes from 192.168.61.197: icmp_seq=1 ttl=64 time=20.7 ms
		64 bytes from 192.168.61.197: icmp_seq=2 ttl=64 time=28.7 ms


	`12.1.1.1` is the gateway for UEs with IP in the range `12.1.1.0/24`. It points tward `oai_spgwu`.


Run bash inside a container by running

	$ docker exec -it <name of the container> /bin/bash

Inside `oai_spgwu`, added a route to forward `10.0.0.0/24` traffic to the 
