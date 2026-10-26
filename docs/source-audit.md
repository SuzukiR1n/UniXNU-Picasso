# 独立源码审计（2026-10-26）

本文件是源码证据，不是设备运行报告。硬件事实来自小米官方仓库；构建接口与组件来自 UniXNU 官方仓库。其他 Picasso 社区移植不作为实现依据。

| 项目 | 源文件与固定提交 | 本仓库决策 |
| --- | --- | --- |
| 构建模型 | UniXNU `759eb61b6b8d475de5b3d1b39e1de1f5294e8d9a`：`scripts/unixnu/`、`examples/device/`、`profiles/`、`components.toml` | 格式 2，独立 SM7250 profile；不继承 SM8550 硬件资源 |
| 定时器 | MiCode/kernel_devicetree `4eeaf08a0472a076aff622bb831dd19f53b1a56a`：`qcom/lito.dtsi` timer，第三组 `<GIC_PPI 3 ...>`，19.2 MHz | 虚拟 INTID = 16 + 3 = 19 |
| GIC | 同上：`interrupt-controller@17a00000` | GICD `0x17a00000/0x10000`；GICR `0x17a60000/0x100000`；stride `0x20000` |
| CPU | 同上：`CPU0..CPU7`、PSCI | MPIDR 0、0x100…0x700；初始只启用 CPU0；PSCI SMC |
| ArmCpu 差异 | UniXNU/ArmCpu `9066b53bbc82e92a98ec44a11dd50fd13eaf1a1b`：`kSgiPpiEnable` 和 IRQ 分派写死 27 | 本地组件解析 ADT timer 的第三组中断；缺失节点保留 27，错误格式拒绝初始化 |
| 内存 | MiCode `qcom/lito.dtsi` 的 `/memory/reg` 为零，另有大量 reserved-memory | 不把源占位值或 128 GB 存储转换为 DRAM；不编造 handoff 窗口 |
| UFS | 同上 `ufshc@1d84000`，SPI 265，PHY `0x1d87000/0xe00` | 只登记禁用节点，不继承 SM8550 时钟、PHY、SMMU 或 GPT |
| 触控 | `qcom/picasso-sm7250.dtsi` 与 `lito-qupv3.dtsi` | GENI SPI SE7 `0x984000/0x4000`，GPIO4 reset、GPIO5 IRQ；NT36672C 多固件变体待实机选型 |
| 固件 | Project-Silicium/Mu-Silicium `4cba43c90e02cdbefbcd9fcdbda33d2328deaec0` 的 tree | 没有 Picasso 平台/配置；没有把 phoenix（K30 4G）当作 Picasso |

DTS 转换使用官方 `scripts/unixnu/devicetree.py`：FDT 大端 GIC specifier 转为 ADT 小端 u32，然后由驱动 `memcpy` 读取；没有改写官方转换器。GIC 地址在本仓库使用正确的根节点 2/2 cell 格式，避免照搬 vendor 源文件的宽度不一致。定时器节点以 `unixnu,adt-name = "timer"` 导出。

`tests/timer_ppi.cpp` 覆盖 19、27、31、超范围 PPI、SPI 类型、长度与空输入；`scripts/check-device.py --dtc` 使用真实 dtc 和官方解析器检查地址、stride、字节序及无内存时拒绝生成 ADT。这些检查均不能替代 CNTFRQ/CNTV、GIC 状态和设备中断计数的实测。

RAM、固件、boot header、framebuffer、GPT、存储写入和启动成功尚无本仓库设备证据。宿主机的完整内核/EFI 构建结果以本仓库 Actions 日志为准。

主要资料：

- [小米官方 Lito DTS](https://github.com/MiCode/kernel_devicetree/blob/4eeaf08a0472a076aff622bb831dd19f53b1a56a/qcom/lito.dtsi)
- [小米官方 Picasso DTS](https://github.com/MiCode/kernel_devicetree/blob/4eeaf08a0472a076aff622bb831dd19f53b1a56a/qcom/picasso-sm7250.dtsi)
- [官方 ArmCpu 源码](https://github.com/UniXNU/ArmCpu/blob/9066b53bbc82e92a98ec44a11dd50fd13eaf1a1b/ArmCpu.cpp)
- [UniXNU 设备树规则](https://unixnu.com/porting/device-tree)
- [UniXNU 固件集成规则](https://unixnu.com/porting/uefi-firmware)
