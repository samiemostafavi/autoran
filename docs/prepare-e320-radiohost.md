# Prepare E320 and the Radio Host

## Setting Up the Host

Rule of thumb is to stick with an up-to-date develop branch of openairinterface and UHD driver. Then set the operating system according to their recommendation. The latest tests show that you should avoid `lowlatency` kernels. The operating sysytems that work are:
- Ubuntu 18.04-generic
    ```console
    $ uname -a
    Linux finarfin 5.4.0-135-generic #152~18.04.2-Ubuntu SMP Tue Nov 29 08:23:49 UTC 2022 x86_64 x86_64 x86_64 GNU/Linux
    ```
- Ubuntu 20.04-generic

Next, we need to install UHD driver on the host. The UHD host version on the E320 must be equal to the one on the host. After installing the desired UHD version on the host, we have to update the radio's UHD if they are not matched.

``` bash
sudo apt install -y libboost-all-dev libusb-1.0-0-dev doxygen python3-docutils python3-mako python3-numpy python3-requests python3-ruamel.yaml python3-setuptools cmake build-essential


git clone https://github.com/EttusResearch/uhd.git ~/uhd
cd ~/uhd
git checkout v4.3.0.0
cd host
mkdir build
cd build
cmake ../
make -j $(nproc)
make test # This step is optional
sudo make install
sudo ldconfig
sudo uhd_images_downloader
```

## Setting Up the Streaming Connection

We use the SFP+ port on the E320 for the radio samples streaming and the RJ45 1Gb interface for the management. 
You need to make sure that the link there is a network connection between SDR and the host with 10G bandwidth and 9000 MTU.
Assume interface `enp101s0f0` is chosen on the host for the streaming.

1. Make sure the FPGA image on the E320 is `XG`
    ```console
    $ uhd_usrp_probe --args="type=e3xx"
    [INFO] [UHD] linux; GNU C++ version 7.5.0; Boost_106501; UHD_4.3.0.HEAD-0-g1f8fd345
    [INFO] [MPMD] Initializing 1 device(s) in parallel with args: mgmt_addr=10.40.3.3,type=e3xx,product=e320,serial=3238B87,name=ni-e320-3238B87,fpga=XG,claimed=False,addr=10.40.3.3
    [INFO] [MPM.PeriphManager] init() called with device args `fpga=XG,mgmt_addr=10.40.3.3,name=ni-e320-3238B87,product=e320'.
    ```
    load the `XG` image if it is not
    ```console
    $ uhd_images_downloader -t e320 -t fpga
    $ uhd_image_loader --args "type=e3xx,mgmt_addr=192.168.2.4,fpga=XG"
    ```

2. Check that it supports 10G (`Supported link modes`) and the speed (`Speed`) is 10G when the link is up
    ```console
    $ sudo ethtool enp101s0f0
    Settings for enp101s0f0:
        Supported ports: [ FIBRE ]
        Supported link modes:   10000baseT/Full 
        Supported pause frame use: Symmetric
        Supports auto-negotiation: No
        Supported FEC modes: Not reported
        Advertised link modes:  10000baseT/Full 
        Advertised pause frame use: Symmetric
        Advertised auto-negotiation: No
        Advertised FEC modes: Not reported
        Speed: 10000Mb/s
        Duplex: Full
        Port: Direct Attach Copper
        PHYAD: 0
        Transceiver: internal
        Auto-negotiation: off
        Supports Wake-on: d
        Wake-on: d
        Current message level: 0x00000007 (7)
                       drv probe link
        Link detected: yes
    ```

3. Verify that the link is up and `mtu` is 9000 on both ends
    
    On the host
    ```console
    $ ip -f inet addr show enp101s0f0
    4: enp101s0f0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9000 qdisc mq state UP group default qlen 1000
    inet 10.40.3.254/16 brd 10.40.255.255 scope global enp101s0f0
       valid_lft forever preferred_lft forever
    ```
    On the E320
    ```console
    root@ni-e320-3238B87:~# ip -f inet addr show sfp0
    115: sfp0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9000 qdisc pfifo_fast qlen 1000
    inet 10.40.3.3/16 brd 10.40.255.255 scope global sfp0
       valid_lft forever preferred_lft forever
    ```
    If it was not, you can set it temporarily by
    ```bash
    sudo ip link set dev enp101s0f0 mtu 9000
    ```
    This won't last after reboot

When running openairinterface gnodeb, enodeb, ue, or nrue, according to B210 defaults it asks UHD for `num_recv_frames=256, num_send_frames=256, product=e320, recv_frame_size=7680, send_frame_size=7680`. If all the above conditions are checkmarked, UHD should be able to set the packet size to at least 1916. This is possible on UHD 4.0 and newer.
```
[INFO] [MPMD] Initializing 1 device(s) in parallel with args: mgmt_addr=10.10.3.3,type=e3xx,product=e320,serial=3238B87,name=ni-e320-3238B87,fpga=XG,claimed=False,addr=10.40.3.3,master_clock_rate=46080000.000000,num_send_frames=256,num_recv_frames=256,send_frame_size=7680,recv_frame_size=7680
[INFO] [MPM.PeriphManager] init() called with device args fpga=XG,master_clock_rate=46080000.000000,mgmt_addr=10.10.3.3,name=ni-e320-3238B87,num_recv_frames=256,num_send_frames=256,product=e320,recv_frame_size=7680,send_frame_size=7680.
...
[HW]   RF board max packet size 1916, size for 100µs jitter 4608 
[HW]   rx_max_num_samps 1916
```

## Host Performance Tuning

1. Check that the network interface ring buffer size is set to max

    ```console
    $ sudo ethtool -g enp101s0f0
    Ring parameters for enp101s0f0:
    Pre-set maximums:
    RX:		4096
    RX Mini:	0
    RX Jumbo:	0
    TX:		4096
    Current hardware settings:
    RX:		512
    RX Mini:	0
    RX Jumbo:	0
    TX:		512
    ```
    and set it with
    ```console
    $ sudo ethtool -G enp101s0f0 tx 4096 rx 4096
    ```
    check the result
    ```console
    $ sudo ethtool -g enp101s0f0
    Ring parameters for enp101s0f0:
    Pre-set maximums:
    RX:		4096
    RX Mini:	0
    RX Jumbo:	0
    TX:		4096
    Current hardware settings:
    RX:		4096
    RX Mini:	0
    RX Jumbo:	0
    TX:		4096
    ```
    
2. Check that the OS network buffers are adjusted
    This is done through our modified version of openairinterface automatically.
    ```console
    $ sudo sysctl net.core.wmem_max net.core.rmem_max net.core.wmem_default net.core.rmem_default
    net.core.wmem_max = 1048576
    net.core.rmem_max = 50000000
    net.core.wmem_default = 212992
    net.core.rmem_default = 212992
    ```
    To set them
    ```console
    sudo sysctl -w net.core.wmem_max=33554432
    sudo sysctl -w net.core.rmem_max=33554432
    sudo sysctl -w net.core.wmem_default=33554432
    sudo sysctl -w net.core.rmem_default=33554432
    ```
    Note that these settings will not persist across a reboot.
 

 3. Disable Hyper-threading
    Check if it is on:
    ```console
    $ sudo cat /sys/devices/system/cpu/smt/active
    1
    ```
    If it returns 1, it means it is on. To disable it:
    ```console
    $ sudo -i
    ~# echo off > /sys/devices/system/cpu/smt/control
    ~# exit
    ```
 
 4. Disable the C-states of the CPU
    ```bash
    sudo apt install linux-tools-common linux-tools-generic
    sudo cpupower idle-set -D 2
    ```
 
 5. Set CPU Governor to `performance`

    Install `cpufrequtils` with the command below:
    ```bash
    sudo apt install cpufrequtils
    ```
    To set the CPU governor to `performance` for all cores:
    ```bash
    for ((i=0;i<$(nproc --all);i++)); do sudo cpufreq-set -c $i -r -g performance; done
    ```
    To verify:
    ```console
    $ cpufreq-info
    cpufrequtils 008: cpufreq-info (C) Dominik Brodowski 2004-2009
    Report errors and bugs to cpufreq@vger.kernel.org, please.
    analyzing CPU 0:
      driver: acpi-cpufreq
      CPUs which run at the same hardware frequency: 0
      CPUs which need to have their frequency coordinated by software: 0
      maximum transition latency: 10.0 us.
      hardware limits: 1.20 GHz - 3.00 GHz
      available frequency steps: 3.00 GHz, 3.00 GHz, 2.90 GHz, 2.70 GHz, 2.60 GHz, 2.50 GHz, 2.40 GHz, 2.20 GHz, 2.10 GHz, 2.00 GHz, 1.80 GHz, 1.70 GHz, 1.60 GHz, 1.50 GHz, 1.30 GHz, 1.20 GHz
      available cpufreq governors: conservative, ondemand, userspace, powersave, performance, schedutil
      current policy: frequency should be within 3.00 GHz and 3.00 GHz.
                      The governor "performance" may decide which speed to use
                      within this range.
      current CPU frequency is 3.80 GHz.
      cpufreq stats: 3.00 GHz:99,92%, 3.00 GHz:0,00%, 2.90 GHz:0,00%, 2.70 GHz:0,00%, 2.60 GHz:0,00%, 2.50 GHz:0,00%, 2.40 GHz:0,00%, 2.20 GHz:0,00%, 2.10 GHz:0,00%, 2.00 GHz:0,00%, 1.80 GHz:0,00%, 1.70 GHz:0,00%, 1.60 GHz:0,00%, 1.50 GHz:0,00%, 1.30 GHz:0,00%, 1.20 GHz:0,08%  (263)
    ...
    ```
 
You can also verify these conditions using the i7z utility, as shown below. 
```console
$ sudo apt-get install i7z
$ sudo i7z

Cpu speed from cpuinfo 2999.00Mhz
cpuinfo might be wrong if cpufreq is enabled. To guess correctly try estimating via tsc
Linux's inbuilt cpu_khz code emulated now
True Frequency (without accounting Turbo) 3000 MHz
  CPU Multiplier 30x || Bus clock frequency (BCLK) 100.00 MHz

Socket [0] - [physical cores=18, logical cores=36, max online cores ever=18]
  TURBO ENABLED on 18 Cores, Hyper Threading ON
  Max Frequency without considering Turbo 3100.00 MHz (100.00 x [31])
  Max TURBO Multiplier (if Enabled) with 1/2/3/4/5/6 Cores is  48x/47x/43x/43x/39x/38x
  Real Current Frequency 3800.00 MHz [100.00 x 38.00] (Max of below)
        Core [core-id]  :Actual Freq (Mult.)      C0%   Halt(C1)%  C3 %   C6 %  Temp      VCore
        Core 1 [0]:       3800.00 (38.00x)       100       0       0       0    60      1.0210
        Core 2 [1]:       3800.00 (38.00x)       100       0       0       0    61      1.0282
        Core 3 [2]:       3800.00 (38.00x)       100       0       0       0    65      1.0205
        Core 4 [3]:       3800.00 (38.00x)       100       0       0       0    65      1.0203
        Core 5 [4]:       3800.00 (38.00x)       100       0       0       0    63      1.0281
        Core 6 [5]:       3800.00 (38.00x)       100       0       0       0    62      1.0208
        Core 7 [6]:       3800.00 (38.00x)       100       0       0       0    63      1.0205
        Core 8 [7]:       3800.00 (38.00x)       100       0       0       0    64      1.0206
        Core 9 [8]:       3800.00 (38.00x)       100       0       0       0    58      1.0211
        Core 10 [9]:      3800.00 (38.00x)       100       0       0       0    62      1.0208
        Core 11 [10]:     3800.00 (38.00x)       100       0       0       0    64      1.0205
        Core 12 [11]:     3800.00 (38.00x)       100       0       0       0    59      1.0137
        Core 13 [12]:     3800.00 (38.00x)       100       0       0       0    65      1.0133
        Core 14 [13]:     3800.00 (38.00x)       100       0       0       0    63      1.0133
        Core 15 [14]:     3800.00 (38.00x)       100       0       0       0    64      1.0133
        Core 16 [15]:     3800.00 (38.00x)       100       0       0       0    65      1.0277
        Core 17 [16]:     3800.00 (38.00x)       100       0       0       0    64      1.0132
        Core 18 [17]:     3800.00 (38.00x)       100       0       0       0    63      1.0
```
 
## Testing the Setup

You can test the SDR setup by running UHD driver examples and tests. 
1. Latency test
    ```console
    $ cd ~/uhd/host/build/examples
    $ ./latency_test 
    
    Summary
    ================
    Number of runs:   1000
    RTT value tested: 1 ms
    ACKs received:    1000/1000
    Underruns:        0
    Late packets:     0
    Other errors:     0
    ```

2. Bandwidth test

    Using one RF card
    ```console
    $ cd ~/uhd/host/build/examples
    $ sudo ./benchmark_rate  \
       --args "type=e3xx,master_clock_rate=61.44e6" \
       --duration 60 \
       --channels "0" \
       --rx_rate 61.44e6 \
       --rx_subdev "A:0" \
       --tx_rate 61.44e6 \
       --tx_subdev "A:0"

    [00:00:06.100430357] Setting device timestamp to 0...
    [00:00:06.109760006] Testing receive rate 61.440000 Msps on 1 channels
    Setting TX spp to 2000
    [00:00:06.155843152] Testing transmit rate 61.440000 Msps on 1 channels
    [00:01:06.158435554] Benchmark complete.

    Benchmark rate summary:
      Num received samples:     3686401959
      Num dropped samples:      0
      Num overruns detected:    0
      Num transmitted samples:  3686456000
      Num sequence errors (Tx): 0
      Num sequence errors (Rx): 0
      Num underruns detected:   0
      Num late commands:        0
      Num timeouts (Tx):        0
      Num timeouts (Rx):        0


    Done!
    ```
    Using two RF cards
    ```console
    $ sudo ./benchmark_rate  \
       --args "type=e3xx,master_clock_rate=61.44e6" \
       --duration 60 \
       --channels "0,1" \
       --rx_rate 30.72e6 \
       --rx_subdev "A:0 A:1" \
       --tx_rate 30.72e6 \
       --tx_subdev "A:0 A:1"

    [00:00:05.872979495] Setting device timestamp to 0...
    [INFO] [MULTI_USRP]     1) catch time transition at pps edge
    [INFO] [MULTI_USRP]     2) set times next pps (synchronously)
    [WARNING] [0/Radio#0] Attempting to set tick rate to 0. Skipping.
    [00:00:07.721876891] Testing receive rate 30.720000 Msps on 2 channels
    [WARNING] [0/Radio#0] Attempting to set tick rate to 0. Skipping.
    Setting TX spp to 2000
    [00:00:07.766649813] Testing transmit rate 30.720000 Msps on 2 channels
    [00:01:07.771522141] Benchmark complete.

    Benchmark rate summary:
      Num received samples:     3686083416
      Num dropped samples:      0
      Num overruns detected:    0
      Num transmitted samples:  3671168000
      Num sequence errors (Tx): 0
      Num sequence errors (Rx): 0
      Num underruns detected:   0
      Num late commands:        0
      Num timeouts (Tx):        0
      Num timeouts (Rx):        0


    Done!
    ```
    As you can see, `spp` is set to 2000. This is another sign of properly configured 10G link.


# References

https://kb.ettus.com/USRP_Host_Performance_Tuning_Tips_and_Tricks
https://kb.ettus.com/Getting_Started_with_4G_LTE_using_Eurecom_OpenAirInterface_(OAI)_on_the_USRP_2974
