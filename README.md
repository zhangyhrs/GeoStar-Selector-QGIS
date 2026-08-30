# GeoStar Selector

GeoStar Selector is an advanced raster selection tool designed for QGIS. It follows a Photoshop-like magic wand workflow and selects spatially connected pixels according to the clicked pixel and a configurable tolerance.

GeoStar Selector 是一款面向 QGIS 用户开发的高级栅格选择工具，采用类似 Photoshop“魔术棒”的交互逻辑，可根据点击位置的像元特征和设定容差，快速识别并选取空间连续、光谱相近的栅格区域。

插件支持新建、添加、减去和相交等多种选择模式，并提供快捷键操作、实时容差调节、四邻域与八邻域连通控制、多区域独立选择、撤销及清除等功能。选择结果可导出为 Shapefile 或 GeoJSON，并继承源栅格的空间参考信息。

## Features

- Photoshop-like magic wand interaction
- New, add, subtract and intersect selection modes
- Real-time tolerance adjustment
- 4-connected and 8-connected region selection
- Multiple independent selections
- Undo, clear and keyboard shortcut support
- Shapefile and GeoJSON export
- Source raster CRS preservation

## Applications

- Remote sensing image interpretation
- Land-cover classification refinement
- Change polygon delineation
- Building and water-body extraction
- Machine-learning sample production
- Raster-to-vector data production

## Requirements

- QGIS 3.x
- NumPy
- OpenCV (cv2)

## Installation

1. Download the repository as a ZIP file.
2. Ensure the ZIP contains a single top-level plugin directory named magicwand_qgis.
3. In QGIS, open Plugins → Manage and Install Plugins → Install from ZIP.
4. Select the ZIP file and enable GeoStar Selector.

## Author

Zhang Y.H. · Yundan Studio
GitHub: @cumtzyh

## License

GNU General Public License v3.0 or later (GPL-3.0-or-later).
