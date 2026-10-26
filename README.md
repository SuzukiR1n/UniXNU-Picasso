# UniXNU for Redmi K30 5G（Picasso / SM7250）

独立移植，采用 [UniXNU 官方源码](https://github.com/UniXNU/UniXNU)和[小米官方 DTS](https://github.com/MiCode/kernel_devicetree/tree/4eeaf08a0472a076aff622bb831dd19f53b1a56a)。**当前处于源码与宿主机构建阶段，尚无可供手机启动的 boot.img，也没有 iOS 桌面运行结果。**

已实现的设备差异：小米 Lito 的虚拟定时器是 PPI 3 / INTID 19，官方 ArmCpu 默认写死 27。本仓库基于官方组件增加设备树解析，并统一修改 GICR 使能和 IRQ 分派。具体依据与边界见 [源码审计](docs/source-audit.md)。不采用其他 Picasso 社区移植的源码、二进制或测试结论。

## 已知设备条件

用户确认 Bootloader 已解锁、存储 128 GB，目前无法连接 ADB。RAM 容量、实际 MIUI 版本、面板供应商、内存图和 GPT 尚未采集。原厂输入研究基线选定 **MIUI V12.5.9.0.RGICNXM / Android 11 / 中国版**，这不是已经在手机验证的固件，也不要求现在刷机。

官方 Mu-Silicium 在锁定版本没有 Picasso 平台。独立 UEFI 平台、GOP、RAM 保留区、UFS 根卷、触控、GPU、Wi-Fi、音频与电源管理仍需开发和验证。完整状态保存在 [porting.toml](porting.toml)。

## GitHub Actions

打开本仓库 **Actions → Picasso build and validation**：推送到 `main` 后自动执行，也支持手动运行。

| 任务 | 内容 | 产物含义 |
| --- | --- | --- |
| `validate` | 格式 2 profile、DTS 编译、FDT/ADT 字节序、定时器边界、移植记录和镜像门槛检查 | 配置解析报告 |
| `package` | Ubuntu 构建官方 UniXNU UEFI 应用 | `UniXNU.efi`，不是手机 UEFI 固件 |
| `kernel` | macOS 构建并预链接 XNU 与本仓库 ArmCpu | 宿主机内核候选，不能直接 fastboot 启动 |

只有任务实际成功且 artifact 中存在相应文件，才算该构建成功。失败任务也保存日志；有日志压缩包不表示镜像构建成功。不自动创建 Release，不自动刷机。源码、组件、OS 和硬件资料的版本均有固定提交。

## 本地校验与构建

Python 3.11+。完整构建使用 macOS；Windows 可以检查配置并运行输入采集工具。首次运行会下载锁定的官方 UniXNU。

```sh
python scripts/unixnu.py --prepare
python scripts/unixnu.py defconfig picasso_defconfig
python scripts/unixnu.py fetch
python scripts/unixnu.py status --json
python scripts/unixnu.py build package
# macOS + Xcode / iPhoneOS SDK / cmake / ninja / unifdef / llvm / lld:
python scripts/unixnu.py build kernel -j 3
```

宿主机安装 `dtc` 和 C++ 编译器后：

```sh
python scripts/check-device.py --upstream .cache/UniXNU --dtc
python .cache/UniXNU/scripts/porting-record.py check --device .
c++ -std=c++11 -Wall -Wextra -Werror -Idrivers/ArmCpu tests/timer_ppi.cpp -o out/timer-ppi
out/timer-ppi
```

如需在 Windows 解析中文移植记录，设置 `PYTHONUTF8=1`。`upstream.rev` 固定构建工具；`sources.lock.toml` 记录硬件资料；`unixnu.lock` 固定官方构建依赖；本地 `socs/sm7250` 与设备代码在同一个提交中版本化。

镜像命令会明确指出缺少的实测输入。请先按 [bring-up 步骤](docs/bring-up.md)采集资料，再继续独立固件适配。通用构建原理见 [UniXNU 官方移植指南](https://unixnu.com/porting/)。

## 许可与来源

原创代码采用 BSD-2-Clause-Patent；官方 ArmCpu 保留其许可证。外部 Linux / 小米源码只引用并锁定，不复制 GPL 驱动或私有固件。详见 [THIRD_PARTY.md](THIRD_PARTY.md)。
