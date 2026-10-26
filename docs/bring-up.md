# Picasso 独立适配与设备验证

当前首先需要原厂输入与独立 UEFI 平台。官方 Mu-Silicium 审计版本没有 Picasso，不能用 K30 4G（phoenix）或 SM8550 固件替代。

## 采集输入

1. 未来可以连接 fastboot 时，将 Android platform-tools 加入 PATH，运行 `powershell -ExecutionPolicy Bypass -File tools/Collect-PicassoInfo.ps1`。脚本仅使用 `getvar`，保存产品型号、解锁状态和可读的分区尺寸，不读取序列号，也不刷机、不擦除。
2. 将原厂 `boot.img`、`dtbo.img` 和固件版本信息放入忽略的 `inputs/`。用 `python scripts/inspect-stock.py inputs/boot.img --output inputs/boot-report.json` 记录 SHA256、Android boot header 和 kernel/ramdisk 尺寸。它不解压、不执行、不刷入镜像。
3. 确认 RAM 容量。待 ADB 或 UEFI 调试条件具备，另行采集 bootloader 修正后的完整 FDT、reserved-memory、UEFI memory map 与 GOP mode。磁盘标称 128 GB 不能用于推导 DRAM。
4. 原厂研究基线是 MIUI V12.5.9.0.RGICNXM / Android 11。先比对设备当前版本与回滚策略；此仓库不提供自动刷原厂固件操作。此版本本身没有在目标手机核验。

原厂镜像解析也不能证明 bootloader 实际加载地址，尤其是 ramdisk 位置和可用连续窗口，需要 handoff 日志交叉检查。

## 开发与验证顺序

| 阶段 | 应取得的结果 |
| --- | --- |
| S0 源码/构建 | 本仓库 Actions 校验、UniXNU 应用、XNU 候选分别成功；审查失败日志 |
| S1 平台 | 独立 SM7250/Picasso DSC/FDF、内存图、原厂二进制来源与哈希、正确的 BootShim/boot header |
| S2 UEFI | CPU、时钟、内存、GOP、按键和日志可用；集成 UniXNU、DarwinBoot、RamDisk、DiskIo、FAT |
| S3 XNU 入口 | 按实际可用内存生成 ADT；单核启动；确认虚拟定时器 INTID 19 是否触发、计数是否增加 |
| S4 存储 | 核对控制器版本、时钟/复位/PHY/SMMU，读取容量、GPT 和已知只读块 |
| S5 用户空间 | 固定 IPSW/ABI/根卷与信任缓存，确认根卷挂载和 launchd；之后再做触控/加速/网络/电源 |

每次测试记录仓库提交、工具链、固件/镜像 SHA256、最后到达阶段、完整日志和下一项测量。只有自己的设备日志可以将 `porting.toml` 改为 `device-verified`。

`hardware.toml` 的资格项不是靠手动全部填 true 就能完成适配：应先补齐各项实测证据、真正的固件 recipe 与完整 DTS，再调整入口的镜像门槛。当前没有 `boot.img` 可供 `fastboot boot`。
