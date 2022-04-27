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

## Turn off hyperthreading

This is not specific for this issue only. For all openairinterface deployments, hyperthreading must be turend off.
In order to disable hyperthreading, turn off Simultaneous Multithreading (SMT) control:

      sudo -i
      cat /sys/devices/system/cpu/smt/active
      echo off > /sys/devices/system/cpu/smt/control
      exit

## Increase `net.core` memory

If it is not embedded in USRP lib file, run the following:

            sudo sysctl -w net.core.wmem_max=62500000, sudo sysctl -w net.core.rmem_max=62500000

The following actions did not make any difference and they all had `LLLLLLLL`s:

1. Changed ethernet link from 1gb to 10gb and vice versa
2. Changed network interface card
3. Set MTU to 1500, 8000, and 9000
4. Changed Openairinterface commit version
5. Used different radios
6. Tried a point-to-point ethernet connection vs using a switch (because it was showing weired behaiviour) 

Finally by switching the kernel to generic from low-latency the issue is gone.

## Change kernel from low-latency to generic 

[here](https://askubuntu.com/questions/838704/grub-reboot-to-specific-kernel) and [here](https://askubuntu.com/questions/1019213/display-grub-menu-and-options-without-rebooting)
      
Use `grub-menu.sh` script to see the installed kernels.

      sudo chmod +x grub-menu.sh
      ./grub-menu.sh short
      
Check the index of the kernel you wish to switch to, e.g. `1>6` and run:

      sudo grub-reboot "1>6"

And reboot

      sudo reboot
      
