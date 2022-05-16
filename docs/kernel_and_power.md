
## Install Low-Latency Kernel

Use `uname -r` to check the kernel version.

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

Still no clue.

## Turn off CPU Power Management

Check [here]<https://askubuntu.com/questions/523640/how-i-can-disable-cpu-frequency-scaling-and-set-the-system-to-performance>

We must set the cpu frequency governor to `performance` first.

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
