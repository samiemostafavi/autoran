# Bad DCI Problem

It means that DCI has not been well decoded.

      bad DCI 1A !!! 
      [PHY]   [UE  0] Frame 1095, subframe 6: Problem in DCI!

From "bad DCI 1A !!!" question by Giuseppe Santaromita in OAI users forum in Oct 2020.
The main problem is with attenuation / amplification, try calibrating your Tx and Rx (at both eNB and UE sides).

## Calibrate Tx Rx Gain and Power

You need to make sure there is no signal saturation, and that also SNR is at an acceptable level.
You can use the command line arguments, and also the eNB config file.

I use the T tracer on both sides to calibrate at eNB side, I have noise at around 20dB, and UE uplink is at around 40dB, and same at UE side (noise around 20dB, downlink around 40dB). If signal goes above 45-50dB, it starts saturating. You play with Rx gain to move noise, and Tx gain to move signal.

# Sudden Late Tx Streaming Problem

When running OAI Enb with USRP E320 and UHD 3.15.0, everything seems normal for 10-20 seconds. But all of a sudden, I get `LLLLLLLLLL`s in the enb logs. There is the same issue with OAI lteUE. Even when I run them together they find each other and establish the connection. But again after a while, one of them gets broken and drops the connection.

In order to resolve the issue, several things needed to be done:

## USRP and Host run the same UHD version 3.15.0

## Increase `net.core` memory

If it is not embedded in USRP lib file, run the following:

            sudo sysctl -w net.core.wmem_max=62500000, sudo sysctl -w net.core.rmem_max=62500000

## Unsuccessful Changes

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
13. Increase ethernet network interface buffer
If you face bursty drops in the network interface, you could try increasing the buffers (if your NIC allows you to): check the maximum setting with:     

            sudo ethtool -g eno1
            
            Ring parameters for eno1:
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
and set it with

            sudo ethtool -G eno1 rx 4096
            

# Most critical workaround

Rebuild the UHD image and openairinterface. Update the UHD version.

