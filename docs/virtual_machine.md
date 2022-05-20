According the questions in the forum, 2GB RAM is needed for linking and compilation of eNB and 4GB for gNB.

The footprint on the filesystem is about 10-12 GBytes.

--

The virtual machine must support C_FLAGS_PROCESSORs used during the compilation: -mavx2 -msse4.1 -mssse3

Try `cat proc/cpuinfo | grep avx2`. If you have an answer then your processor supports AVX2 SIMD instructions.

--

can the Ubuntu server run multiple instances of eNB
and UE for example?

if you want to run in simulation, it should work.

With realtime radio, you can try, expect realtime problems,
but why not. Just try and see.

--

Be sure that SCTP is enabled between eNB and EPC. Virtual
machines, docker, all this "modernity" tends to disable
SCTP.
