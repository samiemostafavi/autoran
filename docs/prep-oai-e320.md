# Modify Openairinterface to Work with USRP E320

Since E320 and B210 have the same RF front-end AD9361, the approach is to make oai believe that the radio is B210. Then it will use the calibration tables of AD9361 for E320 as well. However, E320 is a networked device and from this perspective it is similar to X300 or N3XX USRPs. We make sure to set proper parameters if they are related to the host-sdr link characteristics.

The only file that we modify is `radio/USRP/USERSPACE/LIB/usrp_lib.cpp` in the root folder of `openairinterface5g` repository.

``` console
$ cd ~/openairinterface5g
$ vim radio/USRP/USERSPACE/LIB/usrp_lib.cpp
```

## Add identification block

Look for the following `if` block where b200 device type is set:
```cpp
if (device_adds[0].get("type") == "b200") {
  device->type = USRP_B200_DEV;
  usrp_master_clock = 30.72e6;
  args += boost::str(boost::format(",master_clock_rate=%f") % usrp_master_clock);
  args += ",num_send_frames=256,num_recv_frames=256, send_frame_size=7680, recv_frame_size=7680" ;
}
```
Add the following block right after it:
```cpp
// E320 identification block
// added by Samie Mostafavi
bool device_e3xx = false;
if (device_adds[0].get("type") == "e3xx") {
  device->type = USRP_B200_DEV;
  device_e3xx = true;
  usrp_master_clock = 46.08e6;
  args += boost::str(boost::format(",master_clock_rate=%f") % usrp_master_clock);
  args += ",num_send_frames=256,num_recv_frames=256, send_frame_size=7680, recv_frame_size=7680";

  if ( 0 != system("sysctl -w net.core.rmem_max=62500000 net.core.wmem_max=62500000") )
    LOG_W(HW,"Can't set kernel parameters for e3x0\n");
}
// E320 identification block
```

As you can see, `device->type` is set to `USRP_B200_DEV` and we set the `usrp_master_clock` to 46.08 Mhz from the begining to avoid RX/TX rate known issue.

## Modify `tx_sample_advance` setting

Change the following `switch` block
```cpp
switch ((int)openair0_cfg[0].sample_rate) {
  case 46080000:
    s->usrp->set_master_clock_rate(46.08e6);
    //openair0_cfg[0].samples_per_packet    = 1024;
    openair0_cfg[0].tx_sample_advance     = 115;
    openair0_cfg[0].tx_bw                 = 40e6;
    openair0_cfg[0].rx_bw                 = 40e6;
    break;

  case 30720000:
    s->usrp->set_master_clock_rate(30.72e6);
    //openair0_cfg[0].samples_per_packet    = 1024;
    openair0_cfg[0].tx_sample_advance     = 115;
    openair0_cfg[0].tx_bw                 = 20e6;
    openair0_cfg[0].rx_bw                 = 20e6;
    break;

  case 23040000:
    s->usrp->set_master_clock_rate(23.04e6); //to be checked
    //openair0_cfg[0].samples_per_packet    = 1024;
    openair0_cfg[0].tx_sample_advance     = 113;
    openair0_cfg[0].tx_bw                 = 20e6;
    openair0_cfg[0].rx_bw                 = 20e6;
    break;

  case 15360000:
    s->usrp->set_master_clock_rate(30.72e06);
    //openair0_cfg[0].samples_per_packet    = 1024;
    openair0_cfg[0].tx_sample_advance     = 103;
    openair0_cfg[0].tx_bw                 = 20e6;
    openair0_cfg[0].rx_bw                 = 20e6;
    break;

  case 7680000:
    s->usrp->set_master_clock_rate(30.72e6);
    //openair0_cfg[0].samples_per_packet    = 1024;
    openair0_cfg[0].tx_sample_advance     = 80;
    openair0_cfg[0].tx_bw                 = 20e6;
    openair0_cfg[0].rx_bw                 = 20e6;
    break;

  case 1920000:
    s->usrp->set_master_clock_rate(30.72e6);
    //openair0_cfg[0].samples_per_packet    = 1024;
    openair0_cfg[0].tx_sample_advance     = 40;
    openair0_cfg[0].tx_bw                 = 20e6;
    openair0_cfg[0].rx_bw                 = 20e6;
    break;

  default:
    LOG_E(HW,"Error: unknown sampling rate %f\n",openair0_cfg[0].sample_rate);
    exit(-1);
    break;
}

```
to
```cpp
switch ((int)openair0_cfg[0].sample_rate) {
  case 46080000:
    s->usrp->set_master_clock_rate(46.08e6);
    //openair0_cfg[0].samples_per_packet    = 1024;
    if (device_e3xx) {
      openair0_cfg[0].tx_sample_advance     = 15;
    } else {
      openair0_cfg[0].tx_sample_advance     = 115;
    }
    openair0_cfg[0].tx_bw                 = 40e6;
    openair0_cfg[0].rx_bw                 = 40e6;
    break;

  case 30720000:
    s->usrp->set_master_clock_rate(30.72e6);
    //openair0_cfg[0].samples_per_packet    = 1024;
    if (device_e3xx) {
      openair0_cfg[0].tx_sample_advance     = 15;
    } else {
      openair0_cfg[0].tx_sample_advance     = 115;
    }
    openair0_cfg[0].tx_bw                 = 20e6;
    openair0_cfg[0].rx_bw                 = 20e6;
    break;

  case 23040000:
    s->usrp->set_master_clock_rate(23.04e6); //to be checked
    //openair0_cfg[0].samples_per_packet    = 1024;
    if (device_e3xx) {
      openair0_cfg[0].tx_sample_advance     = 15;
    } else {
      openair0_cfg[0].tx_sample_advance     = 113;
    }
    openair0_cfg[0].tx_bw                 = 20e6;
    openair0_cfg[0].rx_bw                 = 20e6;
    break;
    
  case 15360000:
    s->usrp->set_master_clock_rate(30.72e06);
    //openair0_cfg[0].samples_per_packet    = 1024;
    if (device_e3xx) {
      openair0_cfg[0].tx_sample_advance     = 45;
    } else {
      openair0_cfg[0].tx_sample_advance     = 103;
    }
    openair0_cfg[0].tx_bw                 = 20e6;
    openair0_cfg[0].rx_bw                 = 20e6;
    break;

  case 7680000:
    s->usrp->set_master_clock_rate(30.72e6);
    //openair0_cfg[0].samples_per_packet    = 1024;
    if (device_e3xx) {
      openair0_cfg[0].tx_sample_advance     = 50;
    } else {
      openair0_cfg[0].tx_sample_advance     = 80;
    }
    openair0_cfg[0].tx_bw                 = 20e6;
    openair0_cfg[0].rx_bw                 = 20e6;
    break;

  case 1920000:
    s->usrp->set_master_clock_rate(30.72e6);
    //openair0_cfg[0].samples_per_packet    = 1024;
    if (device_e3xx) {
      openair0_cfg[0].tx_sample_advance     = 50;
    } else {
      openair0_cfg[0].tx_sample_advance     = 40;
    }
    openair0_cfg[0].tx_bw                 = 20e6;
    openair0_cfg[0].rx_bw                 = 20e6;
    break;

  default:
    LOG_E(HW,"Error: unknown sampling rate %f\n",openair0_cfg[0].sample_rate);
    exit(-1);
    break;
}
```

E320 `tx_sample_advance` parameter is taken from `USRP_N300_DEV`,`USRP_X300_DEV`, and `USRP_X400_DEV` switch case.
