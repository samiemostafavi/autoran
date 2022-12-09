##  Could not set RX rate to 46.080 MHz

This problem took us 2 weeks to discover while it was in front of our eyes all the time. When oai initializes the radio, first it asks for a master clock rate and then a bandwidth. You can see on the erroneous logs that oai asks for 30.720 MHz `master_clock_rate` but then tries to set RX and TX rate to 46.080 MHz. This causes a warning: `Could not set RX rate to 46.080 MHz. Actual rate is 30.720 MHz`. Eventually the rate is 30.720 MHz and not 46.080 MHz which is what oai wants.

Erroneous log:
```
[INFO] [UHD] linux; GNU C++ version 7.5.0; Boost_106501; UHD_4.3.0.HEAD-0-g1f8fd345
[HW]   Found USRP e3xx
[INFO] [MPMD] Initializing 1 device(s) in parallel with args: mgmt_addr=10.10.3.4,type=e3xx,product=e320,serial=3238BB5,name=ni-e320-3238BB5,fpga=XG,claimed=False,addr=10.40.3.4,master_clock_rate=30720000.000000,num_send_frames=256,num_recv_frames=256,send_frame_size=7680,recv_frame_size=7680
[INFO] [MPM.PeriphManager] init() called with device args `fpga=XG,master_clock_rate=30720000.000000,mgmt_addr=10.10.3.4,name=ni-e320-3238BB5,num_recv_frames=256,num_send_frames=256,product=e320,recv_frame_size=7680,send_frame_size=7680'.
[INFO] [0/Radio#0] Performing CODEC loopback test on channel 0 ... 
[INFO] [0/Radio#0] CODEC loopback test passed
[INFO] [0/Radio#0] Performing CODEC loopback test on channel 1 ... 
[INFO] [0/Radio#0] CODEC loopback test passed
[INFO] [0/DmaFIFO#0] BIST passed (Estimated Minimum Throughput: 1361 MB/s)
[INFO] [0/DmaFIFO#0] BIST passed (Estimated Minimum Throughput: 1361 MB/s)
[HW]   Setting clock source to internal
[HW]   Setting time source to internal
-- Using calibration table: calib_table_b210_38
[WARNING] [MULTI_USRP] Could not set RX rate to 46.080 MHz. Actual rate is 30.720 MHz
[HW]   cal 0: freq 3500000000.000000, offset 44.000000, diff 119200000.000000
[HW]   cal 1: freq 2660000000.000000, offset 49.800000, diff 959200000.000000
[HW]   cal 2: freq 2300000000.000000, offset 51.000000, diff 1319200000.000000
[HW]   cal 3: freq 1880000000.000000, offset 53.000000, diff 1739200000.000000
[HW]   cal 4: freq 816000000.000000, offset 57.000000, diff 2803200000.000000
[HW]   RX Gain 0 120.000000 (44.000000) => 76.000000 (max 76.000000)
[WARNING] [MULTI_USRP] Could not set TX rate to 46.080 MHz. Actual rate is 30.720 MHz
[HW]   USRP TX_GAIN:89.75 gain_range:89.75 tx_gain:0.00
[HW]   Actual master clock: 46.080000MHz...
[HW]   Actual clock source internal...
[HW]   Actual time source internal...
[HW]   RF board max packet size 1916, size for 100µs jitter 4608 
[HW]   rx_max_num_samps 1916
[HW]   setting rx channel 0
[HW]   RX Channel 0
[HW]     Actual RX sample rate: 30.720000MSps...
[HW]     Actual RX frequency: 3.619200GHz...
[HW]     Actual RX gain: 76.000000...
[HW]     Actual RX bandwidth: 40.000000M...
[HW]     Actual RX antenna: RX2...
[HW]   TX Channel 0
[HW]     Actual TX sample rate: 30.720000MSps...
[HW]     Actual TX frequency: 3.619200GHz...
[HW]     Actual TX gain: 89.750000...
[HW]     Actual TX bandwidth: 40.000000M...
[HW]     Actual TX antenna: TX/RX...
[HW]     Actual TX packet size: 1916
[HW]   Device timestamp: 2.214592...
[HW]   [RRU] has loaded USRP B200 device.
sleep...
```

I resolved this problem by asking explicitly for a 46.080 MHz `master_clock_rate` from the very begining in `radio/USRP/USERSPACE/LIB/usrp_lib.cpp`. 

Healthy logs
```
[INFO] [UHD] linux; GNU C++ version 7.5.0; Boost_106501; UHD_4.3.0.HEAD-0-g1f8fd345
[HW]   Found USRP e3xx
net.core.rmem_max = 62500000
net.core.wmem_max = 62500000
[INFO] [MPMD] Initializing 1 device(s) in parallel with args: mgmt_addr=10.10.3.4,type=e3xx,product=e320,serial=3238BB5,name=ni-e320-3238BB5,fpga=XG,claimed=False,addr=10.40.3.4,master_clock_rate=46080000.000000,num_send_frames=256,num_recv_frames=256,send_frame_size=7680,recv_frame_size=7680
[INFO] [MPM.PeriphManager] init() called with device args `fpga=XG,master_clock_rate=46080000.000000,mgmt_addr=10.10.3.4,name=ni-e320-3238BB5,num_recv_frames=256,num_send_frames=256,product=e320,recv_frame_size=7680,send_frame_size=7680'.
[INFO] [0/Radio#0] Performing CODEC loopback test on channel 0 ... 
[INFO] [0/Radio#0] CODEC loopback test passed
[INFO] [0/Radio#0] Performing CODEC loopback test on channel 1 ... 
[INFO] [0/Radio#0] CODEC loopback test passed
[INFO] [0/DmaFIFO#0] BIST passed (Estimated Minimum Throughput: 1361 MB/s)
[INFO] [0/DmaFIFO#0] BIST passed (Estimated Minimum Throughput: 1361 MB/s)
[HW]   Setting clock source to internal
[HW]   Setting time source to internal
-- Using calibration table: calib_table_b210_38
[HW]   Sampling rate 46080000.000000
[HW]   Setting tx_sample_advance to 15
[HW]   cal 0: freq 3500000000.000000, offset 44.000000, diff 119200000.000000
[HW]   cal 1: freq 2660000000.000000, offset 49.800000, diff 959200000.000000
[HW]   cal 2: freq 2300000000.000000, offset 51.000000, diff 1319200000.000000
[HW]   cal 3: freq 1880000000.000000, offset 53.000000, diff 1739200000.000000
[HW]   cal 4: freq 816000000.000000, offset 57.000000, diff 2803200000.000000
[HW]   RX Gain 0 120.000000 (44.000000) => 76.000000 (max 76.000000)
[HW]   USRP TX_GAIN:89.75 gain_range:89.75 tx_gain:0.00
[HW]   Actual master clock: 46.080000MHz...
[HW]   Actual clock source internal...
[HW]   Actual time source internal...
[HW]   RF board max packet size 1916, size for 100µs jitter 4608 
[HW]   rx_max_num_samps 1916
[HW]   setting rx channel 0
[HW]   RX Channel 0
[HW]     Actual RX sample rate: 46.080000MSps...
[HW]     Actual RX frequency: 3.619200GHz...
[HW]     Actual RX gain: 76.000000...
[HW]     Actual RX bandwidth: 40.000000M...
[HW]     Actual RX antenna: RX2...
[HW]   TX Channel 0
[HW]     Actual TX sample rate: 46.080000MSps...
[HW]     Actual TX frequency: 3.619200GHz...
[HW]     Actual TX gain: 89.750000...
[HW]     Actual TX bandwidth: 40.000000M...
[HW]     Actual TX antenna: TX/RX...
[HW]     Actual TX packet size: 1916
```

Rerefence: https://kb.ettus.com/E320_Getting_Started_Guide#Verifying_Device_Operation

## Bad DCI 1A

It means that DCI has not been well decoded.

      bad DCI 1A !!! 
      [PHY]   [UE  0] Frame 1095, subframe 6: Problem in DCI!

From "bad DCI 1A !!!" question by Giuseppe Santaromita in OAI users forum in Oct 2020.
The main problem is with attenuation / amplification, try calibrating your Tx and Rx (at both eNB and UE sides).

## Calibrate Tx Rx Gain and Power

You need to make sure there is no signal saturation, and that also SNR is at an acceptable level.
You can use the command line arguments, and also the eNB config file.

I use the T tracer on both sides to calibrate at eNB side, I have noise at around 20dB, and UE uplink is at around 40dB, and same at UE side (noise around 20dB, downlink around 40dB). If signal goes above 45-50dB, it starts saturating. You play with Rx gain to move noise, and Tx gain to move signal.

## Sudden Late Tx Streaming Problem

When running OAI Enb with USRP E320 and UHD 3.15.0, everything seems normal for 10-20 seconds. But all of a sudden, I get `LLLLLLLLLL`s in the enb logs. There is the same issue with OAI lteUE. Even when I run them together they find each other and establish the connection. But again after a while, one of them gets broken and drops the connection.

The following actions did not make any difference and they all had `LLLLLLLL`s:

1. Changed ethernet link from 1gb to 10gb and vice versa
2. Changed network interface card
3. Set MTU to 1500, 8000, and 9000
4. Changed Openairinterface commit version
5. Used different radios
6. Tried a point-to-point ethernet connection vs using a switch (because it was showing weired behaiviour) 
7. Tried `ondemand`, `performance`, etc CPU frequency governors.
8. Tried changing to low-latency and generic kernels.
9. A restart always helps!
10. Keep the governor on `performance`
11. Stay on low-latency kernel, with p-states and c-states disabled
12. Try generic kernel.
13. Increase ethernet network interface ring buffers size
            
**Finally**, I updated the UHD driver to 4.0.0 and it is gone.

