
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


What I have done and the following different scenarios all introduce `LLLLLLLL`:

1. Changed ethernet link from 1gb to 10gb and vice versa
2. Changed network interface card
3. Set MTU to 1500, 8000, and 9000
4. Changed Openairinterface commit version
5. Used different radios
6. Tried a point-to-point ethernet connection vs using a switch (because it was showing weired behaiviour) 


Finally by changing the radio host the problem is gone, the specifications of the system:

      $ hostnamectl status
  
         Static hostname: wlab-develop
               Icon name: computer-desktop
                 Chassis: desktop
              Machine ID: 278576ce941940b68678dd11422bf24b
                 Boot ID: e865fecf8ce54e98853b607c9fbd0b65
        Operating System: Ubuntu 18.04.6 LTS
                  Kernel: Linux 5.4.0-109-generic
            Architecture: x86-64
           
The system has 6 cores with the following configuration:

      processor	: 0
      vendor_id	: GenuineIntel
      cpu family	: 6
      model		: 158
      model name	: Intel(R) Core(TM) i7-8700 CPU @ 3.20GHz
      stepping	: 10
      microcode	: 0xea
      cpu MHz		: 4300.001
      cache size	: 12288 KB
      physical id	: 0
      siblings	: 6
      core id		: 0
      cpu cores	: 6
      apicid		: 0
      initial apicid	: 0
      fpu		: yes
      fpu_exception	: yes
      cpuid level	: 22
      wp		: yes
      flags		: fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc art arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc cpuid aperfmperf pni pclmulqdq dtes64 monitor ds_cpl vmx smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm 3dnowprefetch cpuid_fault epb invpcid_single pti ssbd ibrs ibpb stibp tpr_shadow vnmi flexpriority ept vpid ept_ad fsgsbase tsc_adjust bmi1 hle avx2 smep bmi2 erms invpcid rtm mpx rdseed adx smap clflushopt intel_pt xsaveopt xsavec xgetbv1 xsaves dtherm ida arat pln pts hwp hwp_notify hwp_act_window hwp_epp md_clear flush_l1d
      bugs		: cpu_meltdown spectre_v1 spectre_v2 spec_store_bypass l1tf mds swapgs taa itlb_multihit srbds
      bogomips	: 6399.96
      clflush size	: 64
      cache_alignment	: 64
      address sizes	: 39 bits physical, 48 bits virtual
      power management:


7. Change kernel from low-latency to generic
      
Use `grub-menu.sh` script to see the installed kernels.

      sudo chmod +x grub-menu.sh
      ./grub-menu.sh short
      
Check the index of the kernel you wish to switch to, e.g. `1>6` and run:

      sudo grub-reboot "1>6"

And reboot

      sudo reboot
      
      
