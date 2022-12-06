
Openairinterface tutorial: [here](https://gitlab.eurecom.fr/oai/openairinterface5g/-/wikis/OpenAirKernelMainSetup)

# Install Low-Latency Kernel

Use `uname -r` to check the kernel version. If it is not low latency, install it using
```
sudo apt-get install linux-lowlatency
```

## Switch kernels

Check [here](https://askubuntu.com/questions/838704/grub-reboot-to-specific-kernel) and [here](https://askubuntu.com/questions/1019213/display-grub-menu-and-options-without-rebooting)
      
Use `grub-menu.sh` script to see the installed kernels.

      sudo chmod +x grub-menu.sh
      ./grub-menu.sh short
      
Check the index of the kernel you wish to switch to, e.g. `1>6` and run:

      sudo grub-reboot "1>6"

And reboot

      sudo reboot

# Disable CPU Power Management Features

## Disable Intel's P-State and C-State from GRUB

Add `intel_pstate=disable` to the Linux boot options, i.e 

            sudo vim /etc/default/grub
            GRUB_CMDLINE_LINUX_DEFAULT="quiet intel_pstate=disable processor.max_cstate=1 intel_idle.max_cstate=0 idle=poll" 
            sudo update-grub 

Append `blacklist intel_powerclamp` to the end of `/etc/modprobe.d/blacklist.conf`, to blacklist the `intel_powerclamp` module. If the file does not exist, create one, and add the line into it.

## Disable the C-states of the CPU using shell

``` bash
sudo apt install linux-tools-common linux-tools-lowlatency
sudo cpupower idle-set -D 2
```

## Turn off hyperthreading

### Temporary Way:

This is not specific for this issue only. For all openairinterface deployments, hyperthreading must be turend off.
In order to disable hyperthreading, turn off Simultaneous Multithreading (SMT) control:

      sudo -i
      cat /sys/devices/system/cpu/smt/active
      echo off > /sys/devices/system/cpu/smt/control
      exit
      
### Permanent Way:

Still no clue.

## Turn off CPU Frequency Scaling

Check [here](https://askubuntu.com/questions/523640/how-i-can-disable-cpu-frequency-scaling-and-set-the-system-to-performance)
and [here](https://askubuntu.com/questions/149271/how-to-change-default-scaling-governor-back-to-ondemand)

1. Install `cpufreq` tool by `sudo apt-get install cpufrequtils`.
2. Check frequency scaling settings by `sudo cpufreq-info`:

            cpufrequtils 008: cpufreq-info (C) Dominik Brodowski 2004-2009
            Report errors and bugs to cpufreq@vger.kernel.org, please.
            analyzing CPU 0:
              driver: intel_pstate
              CPUs which run at the same hardware frequency: 0
              CPUs which need to have their frequency coordinated by software: 0
              maximum transition latency: 4294.55 ms.
              hardware limits: 800 MHz - 4.60 GHz
              available cpufreq governors: performance, powersave
              current policy: frequency should be within 800 MHz and 4.60 GHz.
                              The governor "powersave" may decide which speed to use
                              within this range.
              current CPU frequency is 4.16 GHz.
3. You see that there is two governor options: `performance` or `powersave`. (Here there is no `ondemand` which exists for most CPUs).
4. Set all CPUs governors to `performance`:

            for cpu in $(seq 0 $(($(nproc) -1))) ; do sudo cpufreq-set -c $cpu -g performance ; done

There is other ways to change the governor:

### Temporary Way:

Check if the governor is `ondemand` or `performance`:

    cat /sys/devices/system/cpu/cpu[0-9]*/cpufreq/scaling_governor
    
Make all of them `performance` by running:

    sudo echo performance | sudo tee /sys/devices/system/cpu/cpu[0-5]*/cpufreq/scaling_governor

### Permanent Way:

After having installed `cpufrequtils` by `sudo apt-get install cpufrequtils` , look at the info given by the command `cpufreq-info`, then create a file - `sudo vim /etc/default/cpufrequtils` - and write into it as below. (old: `ondemand`)

      GOVERNOR="performance"

Lastly the command to make the change take action and be permanent (except when booting up, that is) `sudo /etc/init.d/cpufrequtils restart`

Run `sudo i7z` and check the cpu frequencies and temprature.
