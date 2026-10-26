# ArmCpu：SM7250 定时器适配

直接基于官方 `UniXNU/ArmCpu` 的 `9066b53bbc82e92a98ec44a11dd50fd13eaf1a1b`，保留原许可证与运行时标识。没有使用其他 Picasso 移植仓库。

唯一功能变更：从 `/arm-io/timer/interrupts` 读取 ARM 定时器第三组 GIC 中断描述，换算 `INTID = PPI + 16`，同时用于 GICR 使能和中断分派。小米 `picasso-r-oss` 的 `qcom/lito.dtsi` 指定虚拟 PPI 3，即 INTID 19。无定时器节点时保留官方默认 27；畸形描述使 GIC 初始化失败。

`ArmTimerPpi.h` 可在宿主机编译测试。完整驱动由 Actions 按实际 XNU 编译记录构建；通过编译仍不代表真机定时器工作。初始 DTS 仅启用 CPU0。
