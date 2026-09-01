# GeoStar Selector for QGIS

[![QGIS](https://img.shields.io/badge/QGIS-3.x-589632?logo=qgis&logoColor=white)](https://plugins.qgis.org/plugins/magicwand_qgis/)
[![Release](https://img.shields.io/github/v/release/zhangyhrs/GeoStar-Selector-QGIS)](https://github.com/zhangyhrs/GeoStar-Selector-QGIS/releases/latest)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](magicwand_qgis/LICENSE)

**[English](README.md) | 简体中文**

---

**GeoStar Selector** 是一款面向 QGIS 的高级栅格选择插件。它采用类似 Photoshop“魔术棒”的交互方式，可根据种子像元、容差和连通规则，提取空间连续且光谱相近的区域；同时支持多边形绘制、组合选择和矢量导出。

> **[直接下载 GeoStar Selector v1.0.1（QGIS 安装 ZIP）](https://github.com/zhangyhrs/GeoStar-Selector-QGIS/releases/download/v1.0.1/GeoStar_Selector_QGIS_v1.0.1.zip)**

## 主要功能

- 魔术棒单击选择：按像元相似度进行连通区域生长
- 多边形选择：左键添加节点，右键完成，`Esc` 取消
- 新建、添加、减去、相交四种选择模式
- 实时容差调整，支持 4 邻域与 8 邻域
- 多区域选择、撤销、清除及快捷键操作
- 支持 RGB、16 位、浮点栅格及 NoData 处理
- 支持超大 GeoTIFF 的可见窗口读取
- 支持未知 CRS 的普通 PNG，以及跨 CRS 处理
- 导出 Shapefile 或 GeoJSON，并保留源栅格 CRS

## 安装方法

### QGIS 官方插件库

在 QGIS 中打开 **插件 → 管理并安装插件**，搜索 **GeoStar Selector** 并安装。

### ZIP 离线安装

1. 点击上方“直接下载”链接。
2. 在 QGIS 中打开 **插件 → 管理并安装插件 → 从 ZIP 安装**。
3. 选择 `GeoStar_Selector_QGIS_v1.0.1.zip` 并启用插件。

> 请勿解压后重新压缩。安装包必须保留唯一顶层目录 `magicwand_qgis`。

## 快捷键

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

## 运行依赖

- QGIS 3.x
- NumPy
- OpenCV（`cv2`）

QGIS 通常自带 NumPy；OpenCV 是否可用取决于本机 QGIS Python 环境。

## 关注与交流

欢迎关注微信公众号 **测绘地信**，获取遥感、测绘与 GIS 技术内容；也可加入知识星球 **测绘地理信息共享中心**，交流软件工具与专业资料。

<table>
  <tr>
    <td align="center" width="50%"><strong>微信公众号：测绘地信</strong></td>
    <td align="center" width="50%"><strong>知识星球：测绘地理信息共享中心</strong></td>
  </tr>
  <tr>
    <td align="center"><img src="assets/wechat-official-account.png" alt="微信公众号：测绘地信" width="100%"></td>
    <td align="center"><img src="assets/knowledge-planet.jpg" alt="知识星球：测绘地理信息共享中心" width="64%"></td>
  </tr>
</table>

## 作者

**Zhang Y.H.** · GitHub [@zhangyhrs](https://github.com/zhangyhrs)

## 许可证

[GNU General Public License v3.0 or later](magicwand_qgis/LICENSE)
