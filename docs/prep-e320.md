# Installing and Preparing an E320 SDR

## Configure network connection

If the device is fresh out of the box, management interface must be setup for ssh. It either needs DHCP, or manual static ip. Below setting up a static ip is explained.

To check if the device is recognized by the UHD driver on the host, run one of the following commands

```
uhd_find_devices
```
    
If the device is not showing up, check the network interfaces and bring them up, or just simply turn on the radios LoL.

### Connect to the device with USB

When the USB cable is connected, check the serial devices connected to the host

```
ls /dev/serial/by-id
```
    
Every E320 series device connected to USB will by default show up as four different devices. The devices labeled `USB_to_UART_Bridge_Controller` are the devices that offer a serial prompt. The first (with the `if00` suffix) connects to the STM32 Microcontroller, whereas the second connects to the ARM CPU.
    
```
sudo screen  /dev/serial/by-id/usb-Silicon_Labs_CP2105_Dual_USB_to_UART_Bridge_Controller_011C1095-if01-port0 115200
```

Enter `root` for the login and empty password.

NOTE: You can exit `screen` by `Ctrl+A` followed by `k` and `y`. Do not keep screen sessions open on the device. It makes it very slow. Use `sudo screen -r` to see detached sessions. If there is any, get in an kill it.

### Configure the network interfaces

Once you are inside the USRP, check the output of `nmcli` device to see who is managing which interface

    networkctl list
    IDX LINK TYPE     OPERATIONAL SETUP      
      1 lo   loopback carrier     unmanaged  
      2 eth0 ether    carrier     configuring
      3 sfp0 ether    no-carrier  configuring
 
Or `networkctl status eth0`:

    * 2: eth0                                                             
                 Link File: /lib/systemd/network/99-default.link          
              Network File: /lib/systemd/network/40-eth0.network          
                      Type: ether                                         
                     State: carrier (configuring)      
                      Path: platform-e000b000.ethernet                    
                    Driver: macb                                          
                HW Address: 00:80:2f:33:b2:b4 (NATIONAL INSTRUMENTS CORP.)
                       MTU: 1500 (min: 68, max: 1500)                     
      Queue Length (Tx/Rx): 1/1                                           
          Auto negotiation: yes                                           
                     Speed: 1Gbps                                         
                    Duplex: full                                          
                      Port: mii

To setup the radio network interfaces, edit these files on UHD 3.15.0.0:

    vim /etc/systemd/network/eth0.network
    vim /etc/systemd/network/sfp0.network

With UHD 4.0.0 and newer:

    vim /lib/systemd/network/40-eth0.network
    vim /lib/systemd/network/40-sfp0.network
    
Then restart `systemd-networkd`:

    systemctl restart systemd-networkd
    
NOTE: Care needs to be taken when editing these files on the device, since `vi` / `vim` sometimes generates undo files (e.g. `/data/network/sfp0.network~`), that systemd-networkd might accidentally pick up.
    
For example, for the development devices, we set the `eth0` interface ip to:

    [Network]
    Address=192.168.2.3/16
    Gateway=192.168.0.1 

In the end, make sure the devices respond to ping and use ssh

    ssh root@192.168.2.3
    uhd_usrp_probe

For some reason, uhd commands do not work over screen and USB. Run them and confirm the UHD version matches the UHD version of the radio host.

The Streming interface is the SFP interface for transferring the data samples and not management purposes. This interface could be setup over ssh as mentioned above, or using Ansible from the radio host.

        ansible-playbook -i 192.168.2.3, e320_if_up.yml --extra-vars "ip=192.168.20.3/24 mtu_bytes=1500"
        ansible-playbook -i 192.168.2.4, e320_if_up.yml --extra-vars "ip=192.168.20.4/24 mtu_bytes=1500"
        
Then, you should be able to ping E320 from the host.

## Update E320's firmware and FPGA

In order to change the UHD version on the radio, you must first load up the desired UHD on your host, and then use `uhd_images_downloader` to pull down the relevant sd-card image.

        uhd_images_downloader -t sdimg -t e320
        [INFO] Using base URL: https://files.ettus.com/binaries/cache/
        [INFO] Images destination: /usr/local/share/uhd/images
        The file size for this target (565.1 MiB) exceeds the download limit (100.0 MiB). Continue downloading? [y/N]y
        233759 kB / 592569 kB (039%) e3xx_e320_sdimg_default-v4.0.0.0.zip

You need to open up E320 front panel with the special driver, and pull out the sdcard. Then, use a card reader.
Identify the device where the microSD card is, run the command:
        
        $ dmesg | tail
        [60921.528591]  sda: sda1 sda2 sda3 sda4

Running the command lsblk again will show these partitions have been unmounted. If they are not (`MOUNTPOINT` is specified) unmount them.
        
        $ lsblk
        NAME           MAJ:MIN RM   SIZE RO TYPE  MOUNTPOINT
       sda      8:16   1 14.9G  0 disk
       ├─sda1   8:17   1   16M  0 part
       ├─sda2   8:18   1  1.9G  0 part
       ├─sda3   8:19   1  1.9G  0 part
       └─sda4   8:20   1   11G  0 part

Write the SD card image using dd to write the disk image

        sudo dd if=/usr/local/share/uhd/images/usrp_e320_fs.sdimg | pv | sudo dd of=/dev/sda bs=1M
        
* there is no indication of progress. So be patient.

To ensure the disk is synchronized, run the sync command:

        sync

This must be done from the corresponding radio host.

        sudo uhd_images_downloader -t e320 -t fpga
        sudo uhd_image_loader --args "type=e3xx,mgmt_addr=192.168.2.4,fpga=XG"

Probe the Device from host

        uhd_usrp_probe --args "mgmt_addr=192.168.10.3,addr=192.168.20.3"
        uhd_usrp_probe --args "type=e3xx"
        uhd_config_info --print-all

### References

https://kb.ettus.com/E320_Getting_Started_Guide
https://kb.ettus.com/Writing_the_USRP_File_System_Disk_Image_to_a_SD_Card

