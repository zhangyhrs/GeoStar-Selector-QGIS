# GeoStar Selector

GeoStar Selector is an advanced raster selection tool designed for QGIS. It follows a Photoshop-like magic wand workflow and selects spatially connected pixels according to the clicked pixel and a configurable tolerance.

GeoStar Selector 是一款面向 QGIS 用户开发的高级栅格选择工具，采用类似 Photoshop“魔术棒”的交互逻辑，可根据点击位置的像元特征和设定容差，快速识别并选取空间连续、光谱相近的栅格区域。

插件支持魔术棒单击与多边形绘制两种提取方式，以及新建、添加、减去和相交等多种选择模式。多边形模式下左键添加节点、右键完成、Esc 取消。选择结果可导出为 Shapefile 或 GeoJSON，并继承源栅格的空间参考信息。

## Features

- Photoshop-like magic wand interaction
- Polygon selection: left-click vertices, right-click to finish, Esc to cancel
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
- OpenCV (`cv2`)

QGIS normally includes NumPy. OpenCV availability depends on the QGIS Python environment used by your installation.

## Technical features

- Synchronizes the layer selected in the plugin panel with the active QGIS layer
- Handles projects and raster layers that use different coordinate reference systems
- Preserves the numeric range of 16-bit and floating-point imagery
- Excludes NoData pixels from region growing
- Prevents selections from different map extents from being combined incorrectly
- Uses all three RGB bands when selecting from color imagery
- Supports ungeoreferenced PNG imagery with an unknown CRS
- Reads only the visible GDAL window for responsive operation on very large GeoTIFF imagery

## Installation

1. Download the repository as a ZIP file.
2. Ensure the ZIP contains a single top-level plugin directory named `magicwand_qgis`.
3. In QGIS, open **Plugins → Manage and Install Plugins → Install from ZIP**.
4. Select the ZIP file and enable **GeoStar Selector**.

## Keyboard shortcuts

- `W`: activate the magic wand
- `Shift+W`: add mode
- `Alt+W`: subtract mode
- `Ctrl+Shift+W`: intersect mode
- `Ctrl++` / `Ctrl+-`: adjust tolerance
- `Ctrl+Z`: undo the latest selection
- `Delete`: clear selections on the current layer
- `Ctrl+Delete`: clear all selections

## Author

Zhang Y.H. · Yundan Studio  
GitHub: [@zhangyhrs](https://github.com/zhangyhrs)

## License

This project is licensed under the GNU General Public License v3.0 or later (`GPL-3.0-or-later`).
