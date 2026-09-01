# GeoStar Selector for QGIS

[![QGIS](https://img.shields.io/badge/QGIS-3.x-589632?logo=qgis&logoColor=white)](https://plugins.qgis.org/plugins/magicwand_qgis/)
[![Release](https://img.shields.io/github/v/release/zhangyhrs/GeoStar-Selector-QGIS)](https://github.com/zhangyhrs/GeoStar-Selector-QGIS/releases/latest)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](magicwand_qgis/LICENSE)

**[中文](#中文说明) | [English](#english)**

---

## 中文说明

**GeoStar Selector** 是一款面向 QGIS 的高级栅格选择插件。它采用类似 Photoshop“魔术棒”的交互方式，可根据种子像元、容差和连通规则，提取空间连续且光谱相近的区域；同时支持多边形绘制、组合选择和矢量导出。

> **[直接下载 GeoStar Selector v1.0.1（QGIS 安装 ZIP）](https://github.com/zhangyhrs/GeoStar-Selector-QGIS/releases/download/v1.0.1/GeoStar_Selector_QGIS_v1.0.1.zip)**

### 主要功能

- 魔术棒单击选择：按像元相似度进行连通区域生长
- 多边形选择：左键添加节点，右键完成，`Esc` 取消
- 新建、添加、减去、相交四种选择模式
- 实时容差调整，支持 4 邻域与 8 邻域
- 多区域选择、撤销、清除及快捷键操作
- 支持 RGB、16 位、浮点栅格及 NoData 处理
- 支持超大 GeoTIFF 的可见窗口读取
- 支持未知 CRS 的普通 PNG，以及跨 CRS 处理
- 导出 Shapefile 或 GeoJSON，并保留源栅格 CRS

### 安装方法

**QGIS 官方插件库**

在 QGIS 中打开 **插件 → 管理并安装插件**，搜索 **GeoStar Selector** 并安装。

**ZIP 离线安装**

1. 点击上方“直接下载”链接。
2. 在 QGIS 中打开 **插件 → 管理并安装插件 → 从 ZIP 安装**。
3. 选择 `GeoStar_Selector_QGIS_v1.0.1.zip` 并启用插件。

> 请勿解压后重新压缩。安装包必须保留唯一顶层目录 `magicwand_qgis`。

### 快捷键

| 操作 | 快捷键 |
|---|---|
| 激活魔术棒 | `W` |
| 添加模式 | `Shift+W` |
| 减去模式 | `Alt+W` |
| 相交模式 | `Ctrl+Shift+W` |
| 调整容差 | `Ctrl++` / `Ctrl+-` |
| 撤销 | `Ctrl+Z` |
| 清除当前选择 | `Delete` |
| 清除全部选择 | `Ctrl+Delete` |

### 运行依赖

- QGIS 3.x
- NumPy
- OpenCV（`cv2`）

QGIS 通常自带 NumPy；OpenCV 是否可用取决于本机 QGIS Python 环境。

---

## English

**GeoStar Selector** is an advanced raster selection plugin for QGIS. It provides a Photoshop-like magic wand workflow for extracting spatially connected and spectrally similar pixels based on a seed pixel, tolerance and connectivity rule. Polygon drawing, combined selection modes and vector export are also supported.

> **[Download GeoStar Selector v1.0.1 (QGIS installation ZIP)](https://github.com/zhangyhrs/GeoStar-Selector-QGIS/releases/download/v1.0.1/GeoStar_Selector_QGIS_v1.0.1.zip)**

### Features

- Magic-wand selection using connected region growing
- Polygon selection: left-click to add vertices, right-click to finish, `Esc` to cancel
- New, add, subtract and intersect selection modes
- Real-time tolerance adjustment
- 4-connected and 8-connected region selection
- Multiple selections, undo, clear and keyboard shortcuts
- RGB, 16-bit, floating-point and NoData raster support
- Visible-window reading for very large GeoTIFF imagery
- Ungeoreferenced PNG and cross-CRS processing
- Shapefile and GeoJSON export with source CRS preservation

### Installation

**QGIS Official Plugin Repository**

Open **Plugins → Manage and Install Plugins** in QGIS, search for **GeoStar Selector**, and click **Install**.

**Install from ZIP**

1. Use the direct download link above.
2. Open **Plugins → Manage and Install Plugins → Install from ZIP**.
3. Select `GeoStar_Selector_QGIS_v1.0.1.zip` and enable the plugin.

> Do not extract and recompress the package. The ZIP must contain one top-level directory named `magicwand_qgis`.

### Keyboard shortcuts

| Action | Shortcut |
|---|---|
| Activate Magic Wand | `W` |
| Add mode | `Shift+W` |
| Subtract mode | `Alt+W` |
| Intersect mode | `Ctrl+Shift+W` |
| Adjust tolerance | `Ctrl++` / `Ctrl+-` |
| Undo | `Ctrl+Z` |
| Clear current selection | `Delete` |
| Clear all selections | `Ctrl+Delete` |

### Requirements

- QGIS 3.x
- NumPy
- OpenCV (`cv2`)

NumPy is normally included with QGIS. OpenCV availability depends on the Python environment bundled with your QGIS installation.

---

## 关注与交流 / Follow & Connect

欢迎关注微信公众号 **测绘地信**，获取遥感、测绘与 GIS 技术内容；也可加入知识星球 **测绘地理信息共享中心**，交流软件工具与专业资料。

Follow the **测绘地信** WeChat Official Account for remote sensing, surveying and GIS content. You can also join the **测绘地理信息共享中心** Knowledge Planet community for tools, resources and technical discussions.

<p align="center">
  <img src="assets/wechat-official-account.png" alt="微信公众号：测绘地信 / WeChat Official Account" width="620">
</p>

<p align="center">
  <img src="assets/knowledge-planet.jpg" alt="知识星球：测绘地理信息共享中心 / Knowledge Planet" width="520">
</p>

---

## Author

**Zhang Y.H.** · GitHub [@zhangyhrs](https://github.com/zhangyhrs)

## License

[GNU General Public License v3.0 or later](magicwand_qgis/LICENSE)
