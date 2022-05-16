
## Install Low-Latency Kernel

### Switch kernels

Check [here](https://askubuntu.com/questions/838704/grub-reboot-to-specific-kernel) and [here](https://askubuntu.com/questions/1019213/display-grub-menu-and-options-without-rebooting)
      
Use `grub-menu.sh` script to see the installed kernels.

      sudo chmod +x grub-menu.sh
      ./grub-menu.sh short
      
Check the index of the kernel you wish to switch to, e.g. `1>6` and run:

      sudo grub-reboot "1>6"

And reboot

      sudo reboot


## Turn off hyperthreading

### Temporary Way:

This is not specific for this issue only. For all openairinterface deployments, hyperthreading must be turend off.
In order to disable hyperthreading, turn off Simultaneous Multithreading (SMT) control:

      sudo -i
      cat /sys/devices/system/cpu/smt/active
      echo off > /sys/devices/system/cpu/smt/control
      exit
      
### Permanent Way:


## Turn off CPU Power Management

We must set the cpu frequency governor to `performance` first.

### Temporary Way:
Check if the governor is `ondemand` or `performance`:

    cat /sys/devices/system/cpu/cpu[0-9]*/cpufreq/scaling_governor
    
Make all of them `performance` by running:

    sudo echo performance | sudo tee /sys/devices/system/cpu/cpu[0-5]*/cpufreq/scaling_governor

Run `sudo i7z` and check the cpu frequencies and temprature.
