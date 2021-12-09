# Expose eNodeB interfaces to UE and vice versa


1. On ENB Host, expose UE ips assigned by LTE through spgw-u:

		$ sudo ip route add 12.1.1.0/24 via 192.168.61.197
		$ ping 12.1.1.2
		PING 12.1.1.2 (12.1.1.2) 56(84) bytes of data.
		64 bytes from 12.1.1.2: icmp_seq=1 ttl=63 time=21.1 ms
		64 bytes from 12.1.1.2: icmp_seq=2 ttl=63 time=27.9 ms

2. On UE Host, expose ENB Host docker bridge interface by:
		
		$ sudo ip route add 192.168.61.192/26 via 12.1.1.1 dev oaitun_ue1
		$ ping 192.168.61.193
		PING 192.168.61.193 (192.168.61.193) 56(84) bytes of data.
		64 bytes from 192.168.61.193: icmp_seq=1 ttl=63 time=42.2 ms
		64 bytes from 192.168.61.193: icmp_seq=2 ttl=63 time=31.3 ms

3. On ENB Host, make a gre tunnel:

		$ sudo ip tunnel add tun0 mode gre remote 12.1.1.2 local 192.168.61.193
		$ sudo ip addr add 172.17.0.1/24 dev tun0
		$ sudo ip link set tun0 up

4. On UE Host, make a gre tunnel:

		$ sudo ip tunnel add tun0 mode gre remote 192.168.61.193 local 12.1.1.2
		$ sudo ip addr add 172.17.0.2/24 dev tun0
		$ sudo ip link set tun0 up
	
5. On UE Host, expose ENB host interfaces:
	
		$ sudo ip route add 10.0.0.0/24 via 172.17.0.1 dev tun0
	
6. On eNB Host, expose UE host interfaces:
	
		$ sudo ip route add 10.0.1.0/24 via 172.17.0.2 dev tun0
		
- On UE Host, undeploy:		
	
		$ sudo ip route del 192.168.61.192/26
		$ sudo ip route del 10.0.0.0/24
		$ sudo ip tunnel del tun0

- On eNB Host, undeploy:
	
		$ sudo ip route del 12.1.1.0/24
		$ sudo ip route del 10.0.1.0/24
		$ sudo ip tunnel del tun0
		
