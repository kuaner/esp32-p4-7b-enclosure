# 第三方资料与许可范围

`LICENSE` 适用于本仓库原创的 CadQuery 源码、外壳 / 喇叭盒 / 底座 / 扩展模板模型、文档及本项目生成的预览和报告。第三方资料与依赖保留各自权利及许可，不因本项目的 MIT 许可而重新授权。

## Waveshare 板卡参考

机械适配依据用户提供的以下原厂资料：

- `ESP32-P4-WIFI6-Touch-LCD-7B_3d-20251108.stp`
- `ESP32-P4-WIFI6-Touch-LCD-7B外形尺寸图-20251108.pdf`
- `ESP32-P4-WIFI6-Touch-LCD-7B外形尺寸图-20251108.dwg`

原始文件、完整板卡模型和派生组件缓存 `design/reference/` 不随本仓库或发布包分发。本项目使用其尺寸及几何作为机械适配与检查参考；预览中的屏幕轮廓用于说明装配关系。

复跑完整板卡检查需要从厂商获取同一原始文件，入口为 [Waveshare 官方资源](https://docs.waveshare.com/ESP32-P4-WIFI6-Touch-LCD-7B/Resources-And-Documents) 和 [产品 Wiki](https://www.waveshare.com/wiki/ESP32-P4-WIFI6-Touch-LCD-7B)。本项目不声明厂商附件的再分发许可。文件哈希记录于 `cad/vendor_reference.json`；新版板卡需要重新适配。

ESP32、Waveshare、Bambu Lab 等名称用于标明兼容对象或检查工具，商标归各自所有者。本项目独立维护，并非厂商官方外壳。

## 喇叭尺寸

喇叭外形及公差按用户提供的尺寸图记录于 `cad/parameters.json`。原图 `design/speaker_dimension_reference.jpg` 保留在本地，不随仓库或发布包分发。不同厂家的 45100 喇叭可能存在差异，请按实物核对。

## 依赖

Python 依赖见 `cad/requirements.txt`，通过包管理器单独安装，不打包其源码或二进制。CadQuery、OCP / Open CASCADE、trimesh、NumPy、VTK、Pillow、Shapely、Rtree、NetworkX 及传递依赖遵循各自许可证。

Bambu Studio 仅用于可选本地切片检查，其应用及内置打印机、材料配置不随本项目分发。
