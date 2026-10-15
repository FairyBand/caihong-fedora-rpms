# Caihong Fedora RPM 仓库

这里维护 OnePlus Pad Pro (`caihong`) 的 Fedora Workstation 44 ARM64 设备适配
RPM。仓库与 rootfs 工程分离，Copr 使用 aarch64 builder 构建；当前版本固定从
`caihong-linux-rootfs` 的 commit `4a343b670fcc5892be01857bc79cdb656a79787e` 取设备数据，外部源码在各 spec 中固定
commit。

当前包边界如下：

| 包 | 内容 | SELinux policy |
| --- | --- | --- |
| `libcamera` | Caihong simple pipeline、simple IPA、GPU soft ISP、qcam、GStreamer、传感器 YAML | 未包含 |
| `plasma-camera` | Caihong Plasma Camera 前端，GNOME 会话中作为 Qt 应用运行 | 未包含 |
| `caihong-ssc` | FastRPC listener、SSC SensorProxy、SSC DSP 配置 | 未包含 |
| `caihong-device-support` | Pogo/触控板 udev、DMA heap、MAC、蓝牙、热点、手写笔、手电筒和启动服务 | 未包含 |
| `caihong-firmware` | ADSP/CDSP、GPU、WLAN/BT、触控和音频相关固件 | 不适用 |
| `caihong-audio` | UCM2 和 AudioReach topology | 不适用 |
| `caihong-qbootctl` | Android A/B 槽检查与标记工具 | 未包含 |
| `caihong-kernel-updater` | 当前槽识别、boot 分区写入和读回校验命令/服务 | 未包含 |
| `caihong-kernel-payload` | 具体 release 的 Image、DTB、boot 镜像和模块 | 未包含 |

除 `caihong-kernel-payload` 外，当前规格已在 Fedora 44 x86_64 构建容器中完成
`rpmbuild -ba` 验证；Copr 的 aarch64 构建仍是发布前的目标架构检查。SSC 中的
厂商 ELF 是预编译 payload，因此不生成 debugsource/debug 子包。

SELinux policy 暂时不打包。首个 Fedora 镜像应使用 permissive 启动，按 SSC、相机、
Pogo/pen、热点、MAC 和 kernel updater 分别收集 `ausearch -m AVC`，确认功能后再
建立小型 policy RPM。不要用一个全局 permissive domain 掩盖所有服务。

## 本地检查

需要 Fedora 44 构建环境和 `rpm-build`：

```sh
rpmspec -P --target=aarch64 SPECS/caihong-device-support.spec >/dev/null
rpmspec -P --target=aarch64 SPECS/caihong-ssc.spec >/dev/null
rpmspec -P --target=aarch64 SPECS/caihong-audio.spec >/dev/null
rpmspec -P --target=aarch64 SPECS/caihong-firmware.spec >/dev/null
rpmspec -P --target=aarch64 SPECS/caihong-qbootctl.spec >/dev/null
rpmspec -P --target=aarch64 SPECS/plasma-camera-caihong.spec >/dev/null
rpmspec -P --target=aarch64 SPECS/caihong-kernel-updater.spec >/dev/null
rpmspec -P --target=aarch64 SPECS/caihong-kernel-payload.spec >/dev/null
```

`caihong-kernel-payload` 需要先生成 release archive，目录必须包含：

```text
Image
caihong.dtb
boot-linux.img
boot-userdata.img
kernel-release
LICENSE
modules/<kernel-release>/
```

该 payload 不在普通 Copr 源码构建中生成；内核和 Android boot v2 镜像仍由内核
发布流水线提供，然后以 source archive 交给 Copr。

## Copr 顺序

先构建并发布 `libcamera`，再构建 `plasma-camera`；其余包可以并行。目标项目建议为
`caihong/fedora-44`，只启用 `aarch64`。设备镜像中必须先启用 Copr，再安装这些包。
官方 `libcamera` 和 `plasma-camera` 源版本由 DNF5 override 排除，避免忘记重建时
回退到 Fedora 包。

每个服务第一次启动都应记录：

```sh
getenforce
systemctl --failed
ausearch -m AVC -ts boot
journalctl -b -u caihong-ssc -u iio-sensor-proxy
```

本仓库不把 permissive 结果当成最终迁移完成；只有 policy RPM 补齐并恢复 enforcing
后，Fedora Workstation 44 设备适配才算完成。
