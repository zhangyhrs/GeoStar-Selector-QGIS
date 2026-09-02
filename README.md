# GeoStar Selector for QGIS

[![QGIS](https://img.shields.io/badge/QGIS-3.x-589632?logo=qgis&logoColor=white)](https://plugins.qgis.org/plugins/magicwand_qgis/)
![Language](https://img.shields.io/badge/language-Python-3776AB?logo=python&logoColor=white)
[![Release](https://img.shields.io/github/v/release/zhangyhrs/GeoStar-Selector-QGIS)](https://github.com/zhangyhrs/GeoStar-Selector-QGIS/releases/latest)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](magicwand_qgis/LICENSE)

**English | [简体中文](README_ZH.md)**

---

**GeoStar Selector** is an advanced raster selection plugin for QGIS. It provides a Photoshop-like magic wand workflow for extracting spatially connected and spectrally similar pixels based on a seed pixel, tolerance and connectivity rule. Polygon drawing, combined selection modes and vector export are also supported.

> **[Download GeoStar Selector v1.0.1 (QGIS installation ZIP)](https://github.com/zhangyhrs/GeoStar-Selector-QGIS/releases/download/v1.0.1/GeoStar_Selector_QGIS_v1.0.1.zip)**

## Features

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

## Installation

### QGIS Official Plugin Repository

Open **Plugins → Manage and Install Plugins** in QGIS, search for **GeoStar Selector**, and click **Install**.

### Install from ZIP

1. Use the direct download link above.
2. Open **Plugins → Manage and Install Plugins → Install from ZIP**.
3. Select `GeoStar_Selector_QGIS_v1.0.1.zip` and enable the plugin.

> Do not extract and recompress the package. The ZIP must contain one top-level directory named `magicwand_qgis`.

## Keyboard shortcuts

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

## Requirements

- QGIS 3.x
- Python / PyQGIS
- NumPy
- OpenCV (`cv2`)

NumPy is normally included with QGIS. OpenCV availability depends on the Python environment bundled with your QGIS installation.

## Project links

[Latest release](https://github.com/zhangyhrs/GeoStar-Selector-QGIS/releases/latest) · [Changelog](CHANGELOG.md) · [Report a bug](https://github.com/zhangyhrs/GeoStar-Selector-QGIS/issues) · [QGIS plugin page](https://plugins.qgis.org/plugins/magicwand_qgis/)

## Follow & Connect

Follow the **测绘地信** WeChat Official Account for remote sensing, surveying and GIS content. You can also join the **测绘地理信息共享中心** Knowledge Planet community for tools, resources and technical discussions.

<table>
  <tr>
    <td align="center" width="50%"><strong>WeChat Official Account: 测绘地信</strong></td>
    <td align="center" width="50%"><strong>Knowledge Planet: 测绘地理信息共享中心</strong></td>
  </tr>
  <tr>
    <td align="center"><img src="assets/wechat-official-account.png" alt="WeChat Official Account: 测绘地信" width="100%"></td>
    <td align="center"><img src="assets/knowledge-planet.jpg" alt="Knowledge Planet: 测绘地理信息共享中心" width="64%"></td>
  </tr>
</table>

## Author

**Zhang Y.H.** · GitHub [@zhangyhrs](https://github.com/zhangyhrs)

Related: [SHP2KMZ Tool](https://github.com/zhangyhrs/SHP2KMZ_Tool) · [Map Tile Downloader](https://github.com/zhangyhrs/map_tile_downloader)

## License

[GNU General Public License v3.0 or later](magicwand_qgis/LICENSE)
