# Third-party provenance

- `drivers/ArmCpu/ArmCpu.cpp` and `Info.plist` originate directly from [UniXNU/ArmCpu](https://github.com/UniXNU/ArmCpu), commit `9066b53bbc82e92a98ec44a11dd50fd13eaf1a1b`. Its BSD-2-Clause-Patent license is preserved in `drivers/ArmCpu/LICENSE`. Local changes parse the architectural virtual timer PPI; see the component README.
- Build tools, ARM64/OS profiles and kernel patches are fetched from [UniXNU/UniXNU](https://github.com/UniXNU/UniXNU), pinned by `upstream.rev`. Their notices remain in that checkout. Apple open-source inputs and other components are fetched separately at upstream/catalog pins.
- Hardware resources in the minimal DTS are independently recorded facts from [MiCode/kernel_devicetree](https://github.com/MiCode/kernel_devicetree), commit `4eeaf08a0472a076aff622bb831dd19f53b1a56a`, branch `picasso-r-oss`. Vendor GPL drivers and vendor DTS implementations are not vendored here.
- [Project-Silicium/Mu-Silicium](https://github.com/Project-Silicium/Mu-Silicium), commit `4cba43c90e02cdbefbcd9fcdbda33d2328deaec0`, was inspected for platform availability only. No firmware binaries are redistributed.

No other Picasso community port is used as a source, binary input, or hardware verification result. Original files in this repository use BSD-2-Clause-Patent unless a file states otherwise. No license is granted here to external Apple IPSW or Xiaomi firmware binaries.
