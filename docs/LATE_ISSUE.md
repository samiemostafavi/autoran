
# Relevant Questions in OAI mailing list

## ERROR_CODE_OVERFLOW (Overflow) 


      Hi,

      I finally managed to make it working. I had to do several things which were suggested by you:
      - first I turned off Hyperthreading in gNB host BIOS
      - I've changed USRP N310 filesystem to 3.15.0 so it's the same as UHD version on gNB host. I succeeded to do it using Mender. I run it via Screen so my ssh connection to server is not affecting process - thank for the hint.
      - I've changed settings with commands: sudo sysctl -w net.core.wmem_max=62500000, sudo sysctl -w net.core.rmem_max=62500000
      - For updating filesystem on USRP I've used XG image, so both port are now running 10Gbps

      Thank you for your help.

      BR
      Marcin

In order to disable hyperthreading, do the following:

Newer Kernels provide a Simultaneous Multithreading (SMT) control.

      sudo -i
      cat /sys/devices/system/cpu/smt/active
      echo off > /sys/devices/system/cpu/smt/control
      exit
