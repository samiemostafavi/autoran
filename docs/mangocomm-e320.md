# Run Mangocomm's WiFi stack on E320

##

We are about to test the MAC software on USRP E320 device. I have been looking into the E320 user guide and I noticed that the initial setup is slightly different than ADRV and that can be problematic for us. The issue is that according to the user guide, we have to swap the E320 factory microSD card for the card with 802.11 boot files. However, we want to be able to switch between the "E320 with NI reference design" and "E320 with 802.11 Mangocomm design" totally hands free (from the host PC).
I would like to know whether it is possible to customize this procedure somehow and stick with the same sdcard and switch between the designs back and forth? or we will face major road blocks?
For example, can we copy the boot files to the sdcard (overwrite) from the host and then reboot the device? (While the device is running Mangocomm design/reference design?)

hi Samie- I'm confident the dual-boot setup you describe is possible, but it will require digging into the stock NI design further than I did.

A few notes that may help:

-You'll have to switch BOOT.bin on the SD card to switch designs, since the NI and Mango designs require different FSBL settings. The Zynq boot ROM always runs the file named BOOT.bin.

-The stock NI SD card has multiple partitions, including a FAT partition with BOOT.bin. The Mango design only uses a FAT partition and should successfully ignore any non-FAT partitions.

-You might be able to rename the BOOT.bin files on the SD card from the u-boot prompt using fatload/fatwrite. I haven't tried this. I'm pretty sure the NI u-boot has a 3 second boot delay; the Mango u-boot can be configured to continue running via uEnv.txt. The u-boot prompt requires a USB/UART connection.

-We will soon post our own PetaLinux reference design for the E320. This design extends our 802.11 MAC/PHY with a Linux driver and bundles these into a single PetaLinux project. The user guide is already updated (https://support.mangocomm.com/docs/wlan-user-guide/usage/petalinux.html), we hope to post the design files next week. This Linux design mounts the SD card so renaming files is easy. I'm not sure whether the NI Linux mounts the SD card by default.

To clarify - the NI Linux definitely uses the SD card, I think the root file system is an ext4 partition on the card. We use a RAM filesystem in our PetaLinux projects. The open question is whether the NI Linux setup mounts the SD card's FAT boot partition by default. In our PetaLinux projects, where we assume the SD card has a single FAT partition, we mount the boot partition by default with an fstab entry. I would guess it's possible to mount the FAT boot partition of the multi-partition SD card manually in either Linux setup.




## Change the contents on the SD-card

Samie:
Does anyone know whether the default NI petalinux on the E320 (in network mode) mounts the SD card or not?
I am asking this because I need to change the BOOT.bin and switch to another design from the host. I cannot remove the old SD card and insert a new one.

Marcus D Leech <patchvonbraun@gmail.com>:
Since this system runs off of the SD card, yes. 

Samie:
Thank you Marcus for your answer.
Actually it seems that the root file system is a separate ext4 partition on the card. 
So the question is whether the NI Linux setup mounts the SD card's FAT boot partition by default or not?

Marcus D Leech <patchvonbraun@gmail.com>:
What does “mount” return when you’re on the system? That will be definitive. 


```
root@ni-e320-3238B97:~# lsblk
NAME        MAJ:MIN RM  SIZE RO TYPE MOUNTPOINT
mmcblk0     179:0    0 14.9G  0 disk 
|-mmcblk0p1 179:1    0   16M  0 part /uboot
|-mmcblk0p2 179:2    0  1.9G  0 part /
|-mmcblk0p3 179:3    0  1.9G  0 part 
`-mmcblk0p4 179:4    0 11.1G  0 part /data
```
```
root@ni-e320-3238B97:~# mount
/dev/mmcblk0p2 on / type ext4 (rw,relatime)
devtmpfs on /dev type devtmpfs (rw,relatime,size=511584k,nr_inodes=127896,mode=755)
sysfs on /sys type sysfs (rw,nosuid,nodev,noexec,relatime)
proc on /proc type proc (rw,relatime)
securityfs on /sys/kernel/security type securityfs (rw,nosuid,nodev,noexec,relatime)
tmpfs on /dev/shm type tmpfs (rw,nosuid,nodev)
devpts on /dev/pts type devpts (rw,relatime,gid=5,mode=620,ptmxmode=000)
tmpfs on /run type tmpfs (rw,nosuid,nodev,mode=755)
tmpfs on /sys/fs/cgroup type tmpfs (ro,nosuid,nodev,noexec,mode=755)
cgroup2 on /sys/fs/cgroup/unified type cgroup2 (rw,nosuid,nodev,noexec,relatime,nsdelegate)
cgroup on /sys/fs/cgroup/systemd type cgroup (rw,nosuid,nodev,noexec,relatime,xattr,name=systemd)
cgroup on /sys/fs/cgroup/freezer type cgroup (rw,nosuid,nodev,noexec,relatime,freezer)
cgroup on /sys/fs/cgroup/blkio type cgroup (rw,nosuid,nodev,noexec,relatime,blkio)
cgroup on /sys/fs/cgroup/devices type cgroup (rw,nosuid,nodev,noexec,relatime,devices)
cgroup on /sys/fs/cgroup/cpu,cpuacct type cgroup (rw,nosuid,nodev,noexec,relatime,cpu,cpuacct)
cgroup on /sys/fs/cgroup/memory type cgroup (rw,nosuid,nodev,noexec,relatime,memory)
cgroup on /sys/fs/cgroup/debug type cgroup (rw,nosuid,nodev,noexec,relatime,debug)
cgroup on /sys/fs/cgroup/net_cls type cgroup (rw,nosuid,nodev,noexec,relatime,net_cls)
cgroup on /sys/fs/cgroup/cpuset type cgroup (rw,nosuid,nodev,noexec,relatime,cpuset)
mqueue on /dev/mqueue type mqueue (rw,nosuid,nodev,noexec,relatime)
fusectl on /sys/fs/fuse/connections type fusectl (rw,nosuid,nodev,noexec,relatime)
configfs on /sys/kernel/config type configfs (rw,nosuid,nodev,noexec,relatime)
debugfs on /sys/kernel/debug type debugfs (rw,nosuid,nodev,noexec,relatime)
tmpfs on /tmp type tmpfs (rw,nosuid,nodev)
tmpfs on /var/volatile type tmpfs (rw,relatime)
/dev/mmcblk0p1 on /uboot type vfat (rw,relatime,sync,fmask=0022,dmask=0022,codepage=437,iocharset=iso8859-1,shortname=mixed,errors=remount-ro)
/dev/mmcblk0p4 on /data type ext4 (rw,relatime)
```
```
root@ni-e320-3238B97:~# cd /uboot/
root@ni-e320-3238B97:/uboot# ls
boot.bin  u-boot.img
```

Hence, it should be possible to change the contents of the SD card while it is working.


# References

https://support.mangocomm.com/docs/wlan-user-guide-v2/usage/usrp-e320/getting_started.html




