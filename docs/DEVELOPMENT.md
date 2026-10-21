# 开发与复现

## 最小构建

使用 Python 3.12 和虚拟环境，依赖见 `cad/requirements.txt`。仓库已包含可直接使用的 STL、STEP、预览和报告。

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r cad/requirements.txt
python cad/check_release.py
python cad/build_design.py
python cad/check_printability.py
```

`check_release.py` 仅依赖标准库，验证发布清单和证据，适合首次构建前运行。构建会覆盖相应导出；STEP 元数据时间可能变化，需重跑必要检查后重新打包生成清单。

Windows 使用 `.venv\Scripts\activate`。Linux 可能需要 `libgl1 libegl1 libopengl0`；离屏渲染还依赖可用的 VTK/OpenGL 后端。CI 执行模型构建与逐层检查，不运行依赖原厂文件的装配检查或 macOS Bambu 切片。

## 原厂配合检查

从 [Waveshare 原厂资源入口](https://docs.waveshare.com/ESP32-P4-WIFI6-Touch-LCD-7B/Resources-And-Documents) 获取 `ESP32-P4-WIFI6-Touch-LCD-7B_3d-20251108.stp`，放入根目录。SHA-256：

```text
f2104dc257ee8575459ddf74404e32faf81e4bcda23a8bfec23b6604c089986c
```

原厂附件可能更新；无法获取此日期文件时请联系厂商。不要直接替换成其他文件：当前坐标和柔性排线排除依赖此文件的组件编号。脚本校验原文件哈希，不改写原件。

```sh
python cad/analyze_board.py
python cad/verify_design.py
```

也可用 `python cad/analyze_board.py /path/to/reference.stp` 指定相同文件。缓存位于 `design/reference/`，不进入 Git 或发布包。`fit_reference.py` 只应用整体坐标平移，完整保留玻璃、LCD、PCB、元件及两根 FPC，不再局部排除排线。`screen_geometry.py` 按 STEP 的两级玻璃轮廓定义前口，并在原排线位置定义两个局部避让；真实排线应力和任意折叠形状仍未仿真。

当前实物反馈要求长边保持不动，短边按较小 STEP 数据收紧。不能只修改玻璃外包尺寸而忽略其 0.25 mm 前沿与后部的不同轮廓。挂钩需检查四组真实接头的双向轴向自由行程，不能仅以远距离拉脱阻挡作为松紧判据。板端插头本体不在原厂模型中，`wire_route.py` 中的插头包络属于待实测预留值。

## 逐层几何与切片

`check_printability.py` 以 0.20 mm 水平截面分析上一层承托、孤岛和两端承托短桥，目标为喇叭盒与底座。主壳侧面接口和顶部相机口仍包含桥接。

可选参考切片使用 macOS Bambu Studio 02.08.02.61 内置 P1S 0.4 mm 和 Generic PETG 配置：

```sh
python cad/check_slice.py
```

默认应用 `/Applications/BambuStudio.app`，可用 `BAMBU_APP` 指定其他 `.app` 路径。脚本使用临时配置、关闭支撑、保持交付方向，记录真实输入哈希、支撑刀路和警告，不修改用户设置。其他应用版本、平台和配置布局尚未适配，不要手改版本字段伪造复现。

## 渲染

先完成模型构建与原厂缓存分析，再运行 `python cad/render_design.py`。脚本尝试寻找系统中文字体；也可用 `CAD_CJK_FONT` 指定 `.ttf` / `.ttc`，例如 Linux 安装 Noto CJK 后：

```sh
CAD_CJK_FONT=/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc python cad/render_design.py
```

预览直接渲染实际 BREP。正式图片为整体、正面、背面、分解、底座、挂槽遮挡、打印方向和配合细节八张，其余裁切图片为本地中间文件。

## 发布流程

模型变更后完成相应检查和渲染，本地只刷新发布清单，不创建 ZIP：

```sh
python cad/package_design.py --manifest-only
python cad/check_release.py
```

提交并推送当前源码、导出、文档及报告后，推送一个发布标签，例如：

```sh
git tag -a model-20261020 -m 'Publish current enclosure models'
git push origin main
git push origin model-20261020
```

日期示例需替换为实际发布日期；同日多次发布可使用 `model-20261020.2`。标签用于标记 Git 提交，不增加并行模型目录。也可以在 Actions 中手动运行 **Release models**，填写已存在的同格式标签；它会检查指定标签的提交并补充或重新上传对应 Release 资产。

[release.yml](../.github/workflows/release.yml) 先调用 CAD 检查流程，验证清单、重建三件 CAD 并做两模块逐层检查。通过后在独立的干净检出中打包**该提交已经检查过的导出文件**，避免将跨平台重建产生的 STEP 元数据变动混入原证据。发布任务只需 Python 标准库与 GitHub CLI。

云端生成唯一完整设计包 `ESP32_P4_7B_current.zip`，并单独上传三份 STL、`assembly.step` 和 `SHA256SUMS.txt`。包内含许可、说明、`AGENTS.md`、开发指南、当前源码和模型；不包含原厂文件、缓存、第三方图片或 G-code。`release_sha256.json` 记录包内文件哈希，其自身不递归纳入清单。Release 任务具有仓库内容写入权限；普通 CAD 检查只有读取权限。

几何变更必须重新生成对应证据。打包检查模型有效性、配合、逐层结果、源码指纹和 STL 切片哈希；不匹配时重跑检查，不要手改 `pass` 字段。CI 不下载原厂文件，不假称在 Linux 复跑了原厂配合检查或 macOS Bambu 切片。发布的是与提交源码及证据对应的模型。

## 坐标与接口

单位 mm，装配 +Y 向上、+Z 向背后；主壳背面 Z=22、模块贴合面 Z=22.2，前玻璃约为 Z=0。STL 经变换后贴床，STEP 保留装配位置。

挂点 X=±62.5，上排 Y=20，下排 Y=−28。上下排方向相反，分别让上挂模块和下托底座由重力落座。`interface.py` 的 `flat_adapter()` 为设计模板，不是额外必打印件；新附件应单独验证承载与安装运动。
