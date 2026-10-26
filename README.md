# UniXNU for Redmi K30 5G（Picasso / SM7250）

独立移植，目标为 **iPhone X 的 iOS 16.7.16（20H392）**，产品 `iPhone10,3`、板型 `d22ap`、A11 `0x8015`。身份和内核 IM4P 摘要已直接从苹果 IPSW 的 BuildManifest 核对。采用 [UniXNU 官方源码](https://github.com/UniXNU/UniXNU)和[小米官方 DTS](https://github.com/MiCode/kernel_devicetree/tree/4eeaf08a0472a076aff622bb831dd19f53b1a56a)。**尚无可供手机启动的 boot.img；iOS 16 的 Darwin 22 ABI 与独立 Picasso UEFI 平台仍需适配。**

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
| `ios16-input-audit` | macOS 读取苹果 manifest、核对内核摘要、解压并检查 Darwin 22 / arm64 | iPhone X iOS 16 输入审计报告，不是已移植内核 |

当前官方工具/原生驱动以 Darwin 23 / iOS 17 ABI 开发。默认配置已停止选择未经 Darwin 22 验证的内核驱动，入口阻止直接沿用旧内核/预链接配方。之前在旧基线上成功的内核构建仅是历史回归结果，不能证明 iOS 16 可用。具体工作见 [iOS 16 适配记录](docs/ios16.md)。

只有任务实际成功且 artifact 中存在相应文件，才算该项成功。失败任务也保存日志；有日志压缩包不表示镜像构建成功。不自动创建 Release，不自动刷机。

## 本地校验与构建

Python 3.11+。完整构建使用 macOS；Windows 可以检查配置并运行输入采集工具。首次运行会下载锁定的官方 UniXNU。

```sh
python scripts/unixnu.py --prepare
python scripts/unixnu.py defconfig picasso_defconfig
python scripts/unixnu.py fetch
python scripts/unixnu.py status --json
python scripts/unixnu.py build package
# 从苹果服务器按成员读取约数十 MB，不下载完整 IPSW：
python scripts/audit-ios16.py --upstream .cache/UniXNU
# macOS 可加 --decode，核对内核的实际 Darwin 版本与 arm64 类型。
```

宿主机安装 `dtc` 和 C++ 编译器后：

```sh
python scripts/check-device.py --upstream .cache/UniXNU --dtc
python .cache/UniXNU/scripts/porting-record.py check --device .
c++ -std=c++11 -Wall -Wextra -Werror -Idrivers/ArmCpu tests/timer_ppi.cpp -o out/timer-ppi
out/timer-ppi
```

如需在 Windows 解析中文移植记录，设置 `PYTHONUTF8=1`。`upstream.rev` 固定构建工具；`sources.lock.toml` 记录硬件资料；`unixnu.lock` 固定官方构建依赖；本地 `socs/sm7250` 与设备代码在同一个提交中版本化。

`build kernel` / `build prelink` 会指出待完成的 iOS 16 ABI 工作；镜像命令会指出缺少的实测输入。请按 [iOS 16 记录](docs/ios16.md)和 [bring-up 步骤](docs/bring-up.md)继续。通用构建原理见 [UniXNU 官方移植指南](https://unixnu.com/porting/)。

## 许可与来源

原创代码采用 BSD-2-Clause-Patent；官方 ArmCpu 保留其许可证。外部 Linux / 小米源码只引用并锁定，不复制 GPL 驱动或私有固件。详见 [THIRD_PARTY.md](THIRD_PARTY.md)。
