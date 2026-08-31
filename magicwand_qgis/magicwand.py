from qgis.PyQt.QtCore import Qt, QTimer, pyqtSignal, QVariant
from qgis.PyQt.QtWidgets import QAction, QApplication, QMessageBox, QToolButton, QMenu, QFileDialog, QShortcut
from qgis.PyQt.QtGui import QIcon, QCursor, QColor, QKeySequence
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsField, QgsFields, QgsFeature, QgsGeometry, QgsPointXY,
    QgsWkbTypes, QgsRasterLayer, QgsRasterBlock, QgsVectorFileWriter, QgsMessageLog,
    Qgis, QgsRectangle, QgsCoordinateReferenceSystem, QgsCoordinateTransform
)
from qgis.gui import QgsMapToolEmitPoint, QgsRubberBand
import numpy as np
import cv2
import os
import json
import traceback
from osgeo import gdal
from typing import Optional, Tuple, List, Dict
from enum import Enum

class SelectionMode(Enum):
    NEW = "new"
    ADD = "add"
    SUBTRACT = "subtract"
    INTERSECT = "intersect"

class MagicWandPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.tool = None
        self.tolerance = 5
        self.connectivity = 4
        self.cached_data: Dict[Tuple, np.ndarray] = {}
        # 修改为存储每个要素的独立mask，支持选择模式
        self.layer_features: Dict[str, List[Dict]] = {}  # key: layer_id, value: list of feature dicts
        self.dock_widget = None
        
        # 添加选择模式
        self.selection_mode = SelectionMode.NEW
        # 提取方式：magic_wand（单击相似区域）或 polygon（绘制范围）
        self.selection_method = "magic_wand"
        
        # 快捷键列表
        self.shortcuts = []

    def initGui(self):
        self.toolbar_button = QToolButton()
        self.toolbar_button.setPopupMode(QToolButton.MenuButtonPopup)

        self.action = QAction("Magic Wand", self.iface.mainWindow())
        self.action.setCheckable(True)
        self.action.triggered.connect(lambda checked=False: self.activate_tool())
        self.action.setToolTip("Magic Wand Selection Tool (W)")


        # logo设置：
        try:
            plugin_dir = os.path.dirname(os.path.realpath(__file__))
            icon_path = os.path.join(plugin_dir, "logo.png")
            if os.path.exists(icon_path):
                icon = QIcon(icon_path)
                self.action.setIcon(icon)
                self.toolbar_button.setIcon(icon)
            else:
                default_icon = self.iface.mainWindow().style().standardIcon(
                    self.iface.mainWindow().style().SP_ComputerIcon
                )
                self.action.setIcon(default_icon)
                self.toolbar_button.setIcon(default_icon)
        except Exception as e:
            default_icon = self.iface.mainWindow().style().standardIcon(
                self.iface.mainWindow().style().SP_ComputerIcon
            )
            self.action.setIcon(default_icon)
            self.toolbar_button.setIcon(default_icon)

        menu = QMenu()

        # 选择模式菜单
        mode_menu = menu.addMenu("Selection Mode")
        
        new_action = mode_menu.addAction("New Selection (W)")
        new_action.triggered.connect(lambda: self.set_selection_mode(SelectionMode.NEW))
        
        add_action = mode_menu.addAction("Add to Selection (Shift+W)")
        add_action.triggered.connect(lambda: self.set_selection_mode(SelectionMode.ADD))
        
        subtract_action = mode_menu.addAction("Subtract from Selection (Alt+W)")
        subtract_action.triggered.connect(lambda: self.set_selection_mode(SelectionMode.SUBTRACT))
        
        intersect_action = mode_menu.addAction("Intersect Selection (Ctrl+Shift+W)")
        intersect_action.triggered.connect(lambda: self.set_selection_mode(SelectionMode.INTERSECT))

        menu.addSeparator()

        tolerance_menu = menu.addMenu("Tolerance")
        for tol in [5, 10, 15, 20, 30, 50]:
            action = tolerance_menu.addAction(f"Tolerance: {tol}")
            action.triggered.connect(lambda checked, t=tol: self.set_tolerance(t))

        connectivity_menu = menu.addMenu("Connectivity")
        conn4_action = connectivity_menu.addAction("4-Connected")
        conn4_action.triggered.connect(lambda: self.set_connectivity(4))
        conn8_action = connectivity_menu.addAction("8-Connected")
        conn8_action.triggered.connect(lambda: self.set_connectivity(8))

        menu.addSeparator()

        clear_action = menu.addAction("Clear Current Layer (Delete)")
        clear_action.triggered.connect(self.clear_current_selection)

        clear_all_action = menu.addAction("Clear All Selections (Ctrl+Delete)")
        clear_all_action.triggered.connect(self.clear_all_selections)

        self.toolbar_button.setDefaultAction(self.action)
        self.toolbar_button.setMenu(menu)
        self.iface.addToolBarIcon(self.action)
        
        # 设置快捷键
        self.setup_shortcuts()
        
        # 延迟导入避免循环导入
        from .magicwand_dockwidget import MagicWandDockWidget
        self.dock_widget = MagicWandDockWidget(self)
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock_widget)
        self.dock_widget.visibilityChanged.connect(self.on_dock_visibility_changed)
        
        # 监听项目图层变化
        QgsProject.instance().layersAdded.connect(self.on_layers_changed)
        QgsProject.instance().layersRemoved.connect(self.on_layers_changed)

        # The dock is visible immediately after the plugin is enabled.  Make
        # the magic-wand map tool active as well; otherwise QGIS keeps its Pan
        # tool active and the canvas cursor remains a hand.
        QTimer.singleShot(0, self.activate_tool)

    def setup_shortcuts(self):
        """设置快捷键"""
        # W both selects the default mode and activates the map tool.  Do not
        # register a second QShortcut for the same key: Qt treats duplicate
        # shortcuts as ambiguous and may invoke neither of them.
        shortcut_activate = QShortcut(QKeySequence("W"), self.iface.mainWindow())
        shortcut_activate.activated.connect(
            lambda: self.set_selection_mode(SelectionMode.NEW)
        )
        self.shortcuts.append(shortcut_activate)
        
        shortcut_add = QShortcut(QKeySequence("Shift+W"), self.iface.mainWindow())
        shortcut_add.activated.connect(lambda: self.set_selection_mode(SelectionMode.ADD))
        self.shortcuts.append(shortcut_add)
        
        shortcut_subtract = QShortcut(QKeySequence("Alt+W"), self.iface.mainWindow())
        shortcut_subtract.activated.connect(lambda: self.set_selection_mode(SelectionMode.SUBTRACT))
        self.shortcuts.append(shortcut_subtract)
        
        shortcut_intersect = QShortcut(QKeySequence("Ctrl+Shift+W"), self.iface.mainWindow())
        shortcut_intersect.activated.connect(lambda: self.set_selection_mode(SelectionMode.INTERSECT))
        self.shortcuts.append(shortcut_intersect)
        
        # 容差调整快捷键
        shortcut_tolerance_up = QShortcut(QKeySequence("Ctrl++"), self.iface.mainWindow())
        shortcut_tolerance_up.activated.connect(self.increase_tolerance)
        self.shortcuts.append(shortcut_tolerance_up)
        
        shortcut_tolerance_down = QShortcut(QKeySequence("Ctrl+-"), self.iface.mainWindow())
        shortcut_tolerance_down.activated.connect(self.decrease_tolerance)
        self.shortcuts.append(shortcut_tolerance_down)
        
        # 清除快捷键
        shortcut_clear = QShortcut(QKeySequence("Delete"), self.iface.mainWindow())
        shortcut_clear.activated.connect(self.clear_current_selection)
        self.shortcuts.append(shortcut_clear)
        
        shortcut_clear_all = QShortcut(QKeySequence("Ctrl+Delete"), self.iface.mainWindow())
        shortcut_clear_all.activated.connect(self.clear_all_selections)
        self.shortcuts.append(shortcut_clear_all)
        
        # 撤销快捷键
        shortcut_undo = QShortcut(QKeySequence("Ctrl+Z"), self.iface.mainWindow())
        shortcut_undo.activated.connect(self.undo_last_selection)
        self.shortcuts.append(shortcut_undo)

    def set_selection_mode(self, mode: SelectionMode):
        """设置选择模式"""
        self.selection_mode = mode
        
        # 更新工具提示
        mode_text = {
            SelectionMode.NEW: "New Selection",
            SelectionMode.ADD: "Add to Selection", 
            SelectionMode.SUBTRACT: "Subtract from Selection",
            SelectionMode.INTERSECT: "Intersect Selection"
        }
        
        self.action.setToolTip(f"Magic Wand - {mode_text[mode]}")
        self.show_message(f"Selection mode: {mode_text[mode]}")
        
        # 更新面板显示
        if self.dock_widget:
            self.dock_widget.update_selection_mode(mode)
        
        # 更新工具光标
        if self.tool:
            self.tool.update_cursor()

        # Changing a selection mode means the user intends to select on the
        # canvas. Reclaim the canvas from Pan/Zoom/Identify tools.
        self.activate_tool()

    def set_selection_method(self, method: str):
        """切换魔术棒单击或多边形绘制提取方式。"""
        if method not in ("magic_wand", "polygon"):
            return
        self.selection_method = method
        if self.tool:
            self.tool.cancel_polygon()
        method_text = "Magic Wand" if method == "magic_wand" else "Polygon Selection"
        self.show_message("Extraction method: {}".format(method_text))
        self.activate_tool()

    def on_dock_visibility_changed(self, visible: bool):
        """Activate selection whenever the GeoStar panel is opened."""
        if visible:
            QTimer.singleShot(0, self.activate_tool)

    def increase_tolerance(self):
        """增加容差"""
        new_tolerance = min(self.tolerance + 1, 100)
        self.set_tolerance(new_tolerance)

    def decrease_tolerance(self):
        """减少容差"""
        new_tolerance = max(self.tolerance - 1, 1)
        self.set_tolerance(new_tolerance)

    def undo_last_selection(self):
        """撤销最后一次选择"""
        layer = self.canvas.currentLayer()
        if layer and layer.id() in self.layer_features:
            features = self.layer_features[layer.id()]
            if features:
                features.pop()
                self.show_message("Last selection undone")
                if self.tool:
                    self.tool.refresh_display()
                if self.dock_widget:
                    self.dock_widget.update_feature_count()

    def on_layers_changed(self):
        """当项目图层发生变化时刷新面板"""
        if self.dock_widget and not self.dock_widget.isHidden():
            try:
                self.dock_widget.refresh_layers()
            except RuntimeError:
                self.recreate_dock_widget()

    def unload(self):
        # 断开信号连接
        try:
            QgsProject.instance().layersAdded.disconnect(self.on_layers_changed)
            QgsProject.instance().layersRemoved.disconnect(self.on_layers_changed)
        except (RuntimeError, TypeError) as e:
            QgsMessageLog.logMessage(
                f"Failed to disconnect project layer signals during unload: {e}",
                "GeoStar Selector",
                Qgis.Warning,
            )
        
        # 清理快捷键
        for shortcut in self.shortcuts:
            try:
                shortcut.setParent(None)
                shortcut.deleteLater()
            except (RuntimeError, TypeError) as e:
                QgsMessageLog.logMessage(
                    f"Failed to remove shortcut during unload: {e}",
                    "GeoStar Selector",
                    Qgis.Warning,
                )
        self.shortcuts.clear()
            
        if self.tool:
            self.tool.cleanup()
        self.clear_cached_data()
        self.iface.removeToolBarIcon(self.action)
        if self.dock_widget:
            self.iface.removeDockWidget(self.dock_widget)
            self.dock_widget.deleteLater()

    def set_tolerance(self, tolerance: int):
        self.tolerance = tolerance
        self.clear_cached_data()
        self.show_message(f"Tolerance set to {tolerance}")
        if self.dock_widget:
            self.dock_widget.tolerance_spin.setValue(tolerance)

    def set_connectivity(self, connectivity: int):
        self.connectivity = connectivity
        self.show_message(f"Connectivity set to {connectivity}-connected")
        if self.dock_widget:
            index = 0 if connectivity == 4 else 1
            self.dock_widget.connectivity_combo.setCurrentIndex(index)

    def clear_current_selection(self):
        layer = self.canvas.currentLayer()
        if layer and layer.id() in self.layer_features:
            self.layer_features[layer.id()].clear()
            self.show_message("Current layer selections cleared")
            if self.tool:
                self.tool.clear_rubber_bands()
            # 安全地更新面板
            if self.dock_widget and not self.dock_widget.isHidden():
                try:
                    self.dock_widget.update_feature_count()
                except RuntimeError:
                    self.recreate_dock_widget()

    def clear_all_selections(self):
        self.layer_features.clear()
        self.show_message("All selections cleared")
        if self.tool:
            self.tool.clear_rubber_bands()
        # 安全地更新面板
        if self.dock_widget and not self.dock_widget.isHidden():
            try:
                self.dock_widget.update_feature_count()
            except RuntimeError:
                self.recreate_dock_widget()

    def clear_cached_data(self):
        self.cached_data.clear()

    def activate_tool(self, checked=True):
        """Make the magic-wand point tool the active QGIS map tool."""
        if not self.tool:
            self.tool = PointTool(self.canvas, self, self.iface)
            # Associate the QAction with this QgsMapTool.  QGIS uses this
            # relationship to deactivate Pan/Zoom and keep the correct action
            # checked while the map tool owns the canvas.
            self.tool.setAction(self.action)
        self.canvas.setMapTool(self.tool)
        self.tool.update_cursor()
        self.canvas.setCursor(QCursor(Qt.CrossCursor))
        self.action.setChecked(True)
        if self.dock_widget:
            self.dock_widget.show()
            self.dock_widget.raise_()

    def deactivate_tool(self):
        self.action.setChecked(False)

    def show_message(self, message: str, level: Qgis.MessageLevel = Qgis.Info):
        self.iface.messageBar().pushMessage("Magic Wand", message, level, duration=3)
        QgsMessageLog.logMessage(message, "Magic Wand", level)

    def get_raster_data(self, layer: QgsRasterLayer, extent: QgsRectangle,
                        width: int, height: int) -> Optional[np.ndarray]:
        cache_key = (layer.id(), extent.toString(), width, height)
        if cache_key in self.cached_data:
            return self.cached_data[cache_key]

        try:
            # Fast path for local GDAL rasters: read only the visible window and
            # resample it directly to the map-canvas size. This avoids millions
            # of QgsRasterBlock.value() calls on large GeoTIFFs.
            fast_arr = self.get_gdal_window(layer, extent, width, height)
            if fast_arr is not None:
                if len(self.cached_data) > 3:
                    oldest_key = next(iter(self.cached_data))
                    del self.cached_data[oldest_key]
                self.cached_data[cache_key] = fast_arr
                return fast_arr

            provider = layer.dataProvider()
            if not provider.isValid():
                return None
            band_count = min(layer.bandCount(), 3)
            bands = []
            for band_no in range(1, band_count + 1):
                block = provider.block(band_no, extent, width, height)
                if not block.isValid():
                    return None
                band = np.array([
                    [block.value(y, x) if not block.isNoData(y, x) else np.nan
                     for x in range(width)]
                    for y in range(height)
                ], dtype=np.float32)
                bands.append(band)

            arr = bands[0] if band_count == 1 else np.stack(bands, axis=2)

            if len(self.cached_data) > 3:
                oldest_key = next(iter(self.cached_data))
                del self.cached_data[oldest_key]
            self.cached_data[cache_key] = arr
            return arr
        except Exception as e:
            self.show_message(f"Error reading raster: {str(e)}", Qgis.Critical)
            return None

    def get_gdal_window(self, layer: QgsRasterLayer, extent: QgsRectangle,
                        width: int, height: int) -> Optional[np.ndarray]:
        """Read the visible raster window efficiently with GDAL."""
        source = layer.source().split('|', 1)[0]
        if not source or not os.path.isfile(source):
            return None

        dataset = gdal.Open(source, gdal.GA_ReadOnly)
        if dataset is None or dataset.RasterCount < 1:
            return None

        geotransform = dataset.GetGeoTransform(can_return_null=True)
        if not geotransform:
            return None

        inverse = gdal.InvGeoTransform(geotransform)
        if inverse is None:
            return None
        # GDAL bindings have returned both inv_gt and (success, inv_gt)
        # across versions; support both forms.
        if len(inverse) == 2 and isinstance(inverse[0], (bool, int)):
            if not inverse[0]:
                return None
            inverse = inverse[1]

        corners = [
            (extent.xMinimum(), extent.yMinimum()),
            (extent.xMinimum(), extent.yMaximum()),
            (extent.xMaximum(), extent.yMinimum()),
            (extent.xMaximum(), extent.yMaximum()),
        ]
        pixels = [gdal.ApplyGeoTransform(inverse, x, y) for x, y in corners]
        px = [p[0] for p in pixels]
        py = [p[1] for p in pixels]
        xoff = int(np.floor(min(px)))
        yoff = int(np.floor(min(py)))
        xend = int(np.ceil(max(px)))
        yend = int(np.ceil(max(py)))

        # The provider fallback correctly pads requests extending beyond the
        # raster. Use the fast path only when the requested window is internal.
        if (xoff < 0 or yoff < 0 or xend > dataset.RasterXSize or
                yend > dataset.RasterYSize or xend <= xoff or yend <= yoff):
            return None

        band_count = min(dataset.RasterCount, 3)
        band_list = list(range(1, band_count + 1))
        data = dataset.ReadAsArray(
            xoff, yoff, xend - xoff, yend - yoff,
            buf_xsize=width, buf_ysize=height,
            band_list=band_list
        )
        if data is None:
            return None

        data = np.asarray(data, dtype=np.float32)
        if band_count == 1:
            arr = data
        else:
            arr = np.moveaxis(data, 0, -1)

        for index, band_no in enumerate(band_list):
            nodata = dataset.GetRasterBand(band_no).GetNoDataValue()
            if nodata is not None:
                if band_count == 1:
                    arr[arr == nodata] = np.nan
                else:
                    band = arr[:, :, index]
                    band[band == nodata] = np.nan
        return arr

    def world_to_pixel(self, world_point: QgsPointXY, extent: QgsRectangle,
                       width: int, height: int) -> Tuple[int, int]:
        x = int((world_point.x() - extent.xMinimum()) / extent.width() * width)
        y = int((extent.yMaximum() - world_point.y()) / extent.height() * height)
        return x, y

    def pixel_to_world(self, pixel_x: int, pixel_y: int, extent: QgsRectangle,
                       width: int, height: int) -> QgsPointXY:
        world_x = extent.xMinimum() + pixel_x / width * extent.width()
        world_y = extent.yMaximum() - pixel_y / height * extent.height()
        return QgsPointXY(world_x, world_y)

    def canvas_to_layer_point(self, point: QgsPointXY, layer: QgsRasterLayer) -> QgsPointXY:
        """Convert a map-canvas point to the raster layer CRS."""
        canvas_crs = self.canvas.mapSettings().destinationCrs()
        if not canvas_crs.isValid() or not layer.crs().isValid() or canvas_crs == layer.crs():
            return point
        transform = QgsCoordinateTransform(canvas_crs, layer.crs(), QgsProject.instance())
        return transform.transform(point)

    def canvas_to_layer_extent(self, extent: QgsRectangle, layer: QgsRasterLayer) -> QgsRectangle:
        """Convert the visible canvas extent to the raster layer CRS."""
        canvas_crs = self.canvas.mapSettings().destinationCrs()
        if not canvas_crs.isValid() or not layer.crs().isValid() or canvas_crs == layer.crs():
            return QgsRectangle(extent)
        transform = QgsCoordinateTransform(canvas_crs, layer.crs(), QgsProject.instance())
        return transform.transformBoundingBox(extent)

    def layer_to_canvas_point(self, point: QgsPointXY, layer: QgsRasterLayer) -> QgsPointXY:
        """Convert a raster-layer point to the map canvas CRS for display."""
        canvas_crs = self.canvas.mapSettings().destinationCrs()
        if not canvas_crs.isValid() or not layer.crs().isValid() or canvas_crs == layer.crs():
            return point
        transform = QgsCoordinateTransform(layer.crs(), canvas_crs, QgsProject.instance())
        return transform.transform(point)

    def flood_fill_selection(self, arr: np.ndarray, seed_point: Tuple[int, int],
                             tolerance: float) -> np.ndarray:
        height, width = arr.shape[:2]
        x, y = seed_point
        if not (0 <= x < width and 0 <= y < height):
            return np.zeros((height, width), dtype=np.uint8)

        seed_value = arr[y, x]
        if not np.all(np.isfinite(seed_value)):
            return np.zeros((height, width), dtype=np.uint8)
        mask = np.zeros((height + 2, width + 2), dtype=np.uint8)
        # Keep the original numeric range. Casting 16-bit or float imagery to
        # uint8 causes wrap-around and invalid selections.
        img = np.ascontiguousarray(
            np.nan_to_num(arr, nan=np.finfo(np.float32).max), dtype=np.float32
        )

        try:
            flags = self.connectivity | cv2.FLOODFILL_MASK_ONLY | (255 << 8)
            channel_count = 1 if arr.ndim == 2 else arr.shape[2]
            diff = tuple(float(tolerance) for _ in range(channel_count))
            cv2.floodFill(img, mask, (x, y), 255,
                          loDiff=diff, upDiff=diff, flags=flags)
            return mask[1:-1, 1:-1]
        except Exception:
            return self.custom_flood_fill(arr, seed_point, seed_value, tolerance)

    def custom_flood_fill(self, arr: np.ndarray, seed_point: Tuple[int, int],
                          seed_value: float, tolerance: float) -> np.ndarray:
        height, width = arr.shape[:2]
        x, y = seed_point
        visited = np.zeros_like(arr, dtype=bool)
        result = np.zeros_like(arr, dtype=np.uint8)

        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)] if self.connectivity == 4 else \
                     [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]

        stack = [(x, y)]
        while stack:
            cx, cy = stack.pop()
            if not (0 <= cx < width and 0 <= cy < height) or visited[cy, cx]:
                continue
            visited[cy, cx] = True
            value = arr[cy, cx]
            if not np.all(np.isfinite(value)):
                continue
            difference = np.max(np.abs(value - seed_value))
            if difference > tolerance:
                continue
            result[cy, cx] = 255
            for dx, dy in directions:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < width and 0 <= ny < height and not visited[ny, nx]:
                    stack.append((nx, ny))
        return result

    def apply_selection_mode(self, new_mask: np.ndarray, layer_id: str,
                             extent: QgsRectangle) -> np.ndarray:
        """应用选择模式逻辑"""
        if self.selection_mode == SelectionMode.NEW:
            # NEW模式：直接返回新mask，不与现有选择合并
            # 这样每次都会创建一个新的独立要素
            return new_mask

        if layer_id not in self.layer_features or not self.layer_features[layer_id]:
            # 如果没有现有要素，就当作NEW模式处理
            return new_mask

        # 获取最后一个要素的mask（只与最近的选择进行操作）
        last_feature = self.layer_features[layer_id][-1]
        last_mask = last_feature['mask']

        # 确保mask尺寸一致
        last_extent = last_feature.get('extent')
        same_extent = last_extent is not None and last_extent.toString() == extent.toString()
        if last_mask.shape != new_mask.shape or not same_extent:
            # 如果尺寸不一致，当作NEW模式处理
            return new_mask

        if self.selection_mode == SelectionMode.ADD:
            return np.logical_or(last_mask, new_mask).astype(np.uint8) * 255
        elif self.selection_mode == SelectionMode.SUBTRACT:
            return np.logical_and(last_mask, ~new_mask.astype(bool)).astype(np.uint8) * 255
        elif self.selection_mode == SelectionMode.INTERSECT:
            return np.logical_and(last_mask, new_mask).astype(np.uint8) * 255

        return new_mask

    def apply_magic_wand(self, point: QgsPointXY):
        layer = self.canvas.currentLayer()
        if self.dock_widget:
            selected_layer_id = self.dock_widget.layer_list.currentData()
            selected_layer = QgsProject.instance().mapLayer(selected_layer_id) if selected_layer_id else None
            if isinstance(selected_layer, QgsRasterLayer):
                layer = selected_layer
                self.iface.setActiveLayer(layer)
        if not isinstance(layer, QgsRasterLayer):
            self.show_message("Please select a raster layer", Qgis.Warning)
            return None
        if not layer.isValid():
            self.show_message("Invalid raster layer", Qgis.Warning)
            return None

        canvas_extent = self.canvas.extent()
        extent = self.canvas_to_layer_extent(canvas_extent, layer)
        settings = self.canvas.mapSettings()
        width = settings.outputSize().width()
        height = settings.outputSize().height()

        arr = self.get_raster_data(layer, extent, width, height)
        if arr is None:
            return None

        layer_point = self.canvas_to_layer_point(point, layer)
        pixel_x, pixel_y = self.world_to_pixel(layer_point, extent, width, height)
        new_mask = self.flood_fill_selection(arr, (pixel_x, pixel_y), self.tolerance)
        if np.sum(new_mask) == 0:
            self.show_message("No pixels selected", Qgis.Info)
            return None

        return self.store_selection_mask(new_mask, layer, extent, width, height)

    def apply_polygon_selection(self, canvas_points: List[QgsPointXY]):
        """将用户绘制的地图多边形转换为栅格掩膜并保存。"""
        if len(canvas_points) < 3:
            self.show_message("Polygon needs at least 3 vertices", Qgis.Warning)
            return None

        layer = self.canvas.currentLayer()
        if self.dock_widget:
            selected_layer_id = self.dock_widget.layer_list.currentData()
            selected_layer = QgsProject.instance().mapLayer(selected_layer_id) if selected_layer_id else None
            if isinstance(selected_layer, QgsRasterLayer):
                layer = selected_layer
                self.iface.setActiveLayer(layer)
        if not isinstance(layer, QgsRasterLayer) or not layer.isValid():
            self.show_message("Please select a valid raster layer", Qgis.Warning)
            return None

        extent = self.canvas_to_layer_extent(self.canvas.extent(), layer)
        settings = self.canvas.mapSettings()
        width = settings.outputSize().width()
        height = settings.outputSize().height()

        pixel_points = []
        for canvas_point in canvas_points:
            layer_point = self.canvas_to_layer_point(canvas_point, layer)
            pixel_points.append(self.world_to_pixel(layer_point, extent, width, height))

        polygon = np.asarray(pixel_points, dtype=np.int32).reshape((-1, 1, 2))
        polygon_mask = np.zeros((height, width), dtype=np.uint8)
        cv2.fillPoly(polygon_mask, [polygon], 255)
        if np.sum(polygon_mask) == 0:
            self.show_message("Polygon does not overlap the current raster view", Qgis.Warning)
            return None

        return self.store_selection_mask(
            polygon_mask, layer, extent, width, height, source_name="Polygon"
        )

    def store_selection_mask(self, new_mask, layer, extent, width, height,
                             source_name="Magic Wand"):
        """统一应用选择模式并保存魔术棒或多边形产生的掩膜。"""
        layer_id = layer.id()
        final_mask = self.apply_selection_mode(new_mask, layer_id, extent)

        if np.sum(final_mask) == 0:
            self.show_message("Selection resulted in empty area", Qgis.Info)
            if self.tool:
                self.tool.clear_rubber_bands()
            return None

        # 初始化图层要素列表
        if layer_id not in self.layer_features:
            self.layer_features[layer_id] = []

        # 根据选择模式处理要素存储
        if self.selection_mode == SelectionMode.NEW:
            # NEW模式：创建新的独立要素
            feature_dict = {
                'mask': final_mask,
                'extent': extent,
                'width': width,
                'height': height,
                'layer_name': layer.name(),
                'layer_crs': layer.crs()
            }
            self.layer_features[layer_id].append(feature_dict)

            pixel_count = np.sum(final_mask > 0)
            feature_count = len(self.layer_features[layer_id])
            self.show_message("{} feature created: {} pixels (Total features: {})".format(
                source_name, pixel_count, feature_count
            ))

        else:
            # ADD/SUBTRACT/INTERSECT模式：修改最后一个要素
            if self.layer_features[layer_id]:
                # 更新最后一个要素
                self.layer_features[layer_id][-1]['mask'] = final_mask

                pixel_count = np.sum(final_mask > 0)
                mode_text = {
                    SelectionMode.ADD: "Added to last feature",
                    SelectionMode.SUBTRACT: "Subtracted from last feature",
                    SelectionMode.INTERSECT: "Intersected with last feature"
                }
                self.show_message("{}: {} pixels".format(mode_text[self.selection_mode], pixel_count))
            else:
                # 如果没有现有要素，创建新要素
                feature_dict = {
                    'mask': final_mask,
                    'extent': extent,
                    'width': width,
                    'height': height,
                    'layer_name': layer.name(),
                    'layer_crs': layer.crs()
                }
                self.layer_features[layer_id].append(feature_dict)
                pixel_count = np.sum(final_mask > 0)
                self.show_message("New feature created: {} pixels".format(pixel_count))

        # 安全地更新面板
        if self.dock_widget and not self.dock_widget.isHidden():
            try:
                self.dock_widget.update_feature_count()
            except RuntimeError:
                self.recreate_dock_widget()

        return final_mask
    # 保持现有的导出和其他方法不变...
    def export_selections(self, export_format='shp'):
        """导出所有选择的要素"""
        if not self.layer_features:
            self.show_message("No features to export", Qgis.Warning)
            return

        # 选择保存路径
        if export_format.lower() == 'shp':
            path, _ = QFileDialog.getSaveFileName(
                None, "Export Features as Shapefile", "", "Shapefile (*.shp)"
            )
            if not path:
                return
            if not path.endswith('.shp'):
                path += '.shp'
        elif export_format.lower() == 'json':
            path, _ = QFileDialog.getSaveFileName(
                None, "Export Features as GeoJSON", "", "GeoJSON (*.json)"
            )
            if not path:
                return
            if not path.endswith('.json'):
                path += '.json'
        else:
            self.show_message("Unsupported export format", Qgis.Warning)
            return

        try:
            # 合并所有图层的要素
            all_features = []
            layer_names = []
            
            for layer_id, features in self.layer_features.items():
                layer = QgsProject.instance().mapLayer(layer_id)
                if not layer or not features:
                    continue
                    
                layer_names.append(layer.name())
                
                for idx, feature_dict in enumerate(features):
                    mask = feature_dict['mask']
                    extent = feature_dict['extent']
                    width = feature_dict['width']
                    height = feature_dict['height']
                    layer_crs = feature_dict['layer_crs']
                    
                    # 查找轮廓
                    contours, _ = cv2.findContours(
                        mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
                    )
                    
                    for contour_idx, contour in enumerate(contours):
                        if len(contour) < 3:
                            continue
                            
                        # 转换像素坐标到世界坐标
                        world_points = []
                        for point in contour:
                            world_pt = self.pixel_to_world(
                                point[0][0], point[0][1], extent, width, height
                            )
                            world_points.append(world_pt)
                        
                        # 确保多边形闭合且有足够的点
                        if len(world_points) > 2:
                            # 检查是否需要闭合
                            if len(world_points) > 0 and world_points[0] != world_points[-1]:
                                world_points.append(world_points[0])
                            
                            try:
                                geom = QgsGeometry.fromPolygonXY([world_points])
                                
                                # 检查几何有效性 - 兼容不同QGIS版本
                                is_valid = False
                                try:
                                    is_valid = geom.isValid()
                                except AttributeError:
                                    # 如果没有isValid方法，检查是否为空
                                    is_valid = not geom.isEmpty()
                                
                                if is_valid and geom.area() > 0:
                                    feature_info = {
                                        'geometry': geom,
                                        'layer_name': layer.name(),
                                        'feature_id': idx + 1,
                                        'contour_id': contour_idx + 1,
                                        'area': geom.area(),
                                        'crs': layer_crs
                                    }
                                    all_features.append(feature_info)
                            except Exception as e:
                                self.show_message(f"Warning: Failed to create geometry for contour {contour_idx}: {str(e)}", Qgis.Warning)
                                continue

            if not all_features:
                self.show_message("No valid features to export. Please ensure your selections contain valid polygons.", Qgis.Warning)
                return

            # 使用第一个要素的CRS作为输出CRS
            output_crs = all_features[0]['crs']
            
            if export_format.lower() == 'json':
                self._export_as_geojson(all_features, path, output_crs)
            else:
                self._export_as_shapefile(all_features, path, output_crs)
                
            self.show_message(f"Successfully exported {len(all_features)} features to {export_format.upper()}")
            
        except Exception as e:
            self.show_message(f"Export failed: {str(e)}", Qgis.Critical)
            # 提供调试信息
            QgsMessageLog.logMessage(f"Export error details: {str(e)}", "Magic Wand", Qgis.Critical)

    def _export_as_shapefile(self, features, path, crs):
        """导出为Shapefile格式"""
        try:
            # 创建内存图层
            crs_string = crs.toWkt() if hasattr(crs, 'toWkt') else crs.authid()
            vl = QgsVectorLayer(f"Polygon?crs={crs_string}", "magic_wand_features", "memory")
            pr = vl.dataProvider()
            
            # 添加字段
            fields = [
                QgsField("layer_name", QVariant.String),
                QgsField("feature_id", QVariant.Int),
                QgsField("contour_id", QVariant.Int),
                QgsField("area", QVariant.Double)
            ]
            pr.addAttributes(fields)
            vl.updateFields()
            
            # 添加要素
            features_added = 0
            for feature_info in features:
                try:
                    feat = QgsFeature()
                    feat.setGeometry(feature_info['geometry'])
                    feat.setAttributes([
                        feature_info['layer_name'],
                        feature_info['feature_id'],
                        feature_info['contour_id'],
                        float(feature_info['area'])
                    ])
                    
                    if pr.addFeature(feat):
                        features_added += 1
                except Exception as e:
                    self.show_message(f"Warning: Failed to add feature to shapefile: {str(e)}", Qgis.Warning)
                    continue
            
            if features_added == 0:
                raise Exception("No features were successfully added to the shapefile")
            
            vl.updateExtents()
            
            # 写入Shapefile
            error = QgsVectorFileWriter.writeAsVectorFormat(
                vl, path, "UTF-8", crs, "ESRI Shapefile"
            )
            
            if error[0] != QgsVectorFileWriter.NoError:
                raise Exception(f"Shapefile export error: {error[1]}")
                
            self.show_message(f"Successfully exported {features_added} features to Shapefile")
            
        except Exception as e:
            raise Exception(f"Shapefile export error: {str(e)}")

    def _export_as_geojson(self, features, path, crs):
        """导出为GeoJSON格式"""
        try:
            geojson_data = {
                "type": "FeatureCollection",
                "crs": {
                    "type": "name",
                    "properties": {
                        "name": crs.authid() if crs.authid() else "EPSG:4326"
                    }
                },
                "features": []
            }
            
            for feature_info in features:
                try:
                    geom = feature_info['geometry']
                    # 安全地获取几何JSON
                    if hasattr(geom, 'asJson'):
                        geom_json_str = geom.asJson()
                    else:
                        # 备用方法
                        geom_json_str = geom.exportToGeoJSON()
                    
                    geom_dict = json.loads(geom_json_str)
                    
                    feature = {
                        "type": "Feature",
                        "geometry": geom_dict,
                        "properties": {
                            "layer_name": feature_info['layer_name'],
                            "feature_id": feature_info['feature_id'],
                            "contour_id": feature_info['contour_id'],
                            "area": float(feature_info['area'])
                        }
                    }
                    geojson_data["features"].append(feature)
                except Exception as e:
                    self.show_message(f"Warning: Failed to export feature to GeoJSON: {str(e)}", Qgis.Warning)
                    continue
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(geojson_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            raise Exception(f"GeoJSON export error: {str(e)}")

    def recreate_dock_widget(self):
        """重新创建面板"""
        try:
            if self.dock_widget:
                self.iface.removeDockWidget(self.dock_widget)
                self.dock_widget.deleteLater()
        except (RuntimeError, TypeError) as e:
            QgsMessageLog.logMessage(
                f"Failed to remove existing dock widget: {e}",
                "GeoStar Selector",
                Qgis.Warning,
            )
        
        from .magicwand_dockwidget import MagicWandDockWidget
        self.dock_widget = MagicWandDockWidget(self)
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock_widget)

    def get_feature_count(self, layer_id=None):
        """获取要素数量"""
        if layer_id:
            return len(self.layer_features.get(layer_id, []))
        else:
            return sum(len(features) for features in self.layer_features.values())


class PointTool(QgsMapToolEmitPoint):
    def __init__(self, canvas, plugin, iface):
        super().__init__(canvas)
        self.canvas = canvas
        self.plugin = plugin
        self.iface = iface
        self.rubber_bands = []
        self.polygon_points = []
        self.polygon_preview = None
        # 使用QColor对象而不是Qt.GlobalColor
        self.colors = [
            QColor(255, 0, 0),      # 红色
            QColor(0, 0, 255),      # 蓝色
            QColor(0, 255, 0),      # 绿色
            QColor(255, 255, 0),    # 黄色
            QColor(255, 0, 255),    # 洋红
            QColor(0, 255, 255),    # 青色
            QColor(255, 128, 0),    # 橙色
            QColor(128, 0, 255),    # 紫色
        ]
        self.update_cursor()

    def update_cursor(self):
        """选择工具在所有模式下都使用精确取样十字光标。"""
        cross_cursor = QCursor(Qt.CrossCursor)
        self.setCursor(cross_cursor)
        # Some QGIS/Qt builds do not immediately propagate QgsMapTool.setCursor
        # after switching away from Pan. Set the canvas cursor as well.
        if self.canvas.mapTool() is self:
            self.canvas.setCursor(cross_cursor)

    def activate(self):
        """Re-apply the precision cursor every time QGIS activates the tool."""
        super().activate()
        self.update_cursor()
        self.canvas.setCursor(QCursor(Qt.CrossCursor))
        self.plugin.action.setChecked(True)

    def canvasReleaseEvent(self, event):
        if self.plugin.selection_method == "polygon":
            if event.button() == Qt.LeftButton:
                self.add_polygon_vertex(self.toMapCoordinates(event.pos()))
            elif event.button() == Qt.RightButton:
                self.finish_polygon()
            return

        if event.button() != Qt.LeftButton:
            return

        # 检查修饰键并设置相应的选择模式
        modifiers = QApplication.keyboardModifiers()
        
        if modifiers == Qt.ShiftModifier:
            original_mode = self.plugin.selection_mode
            self.plugin.set_selection_mode(SelectionMode.ADD)
        elif modifiers == Qt.AltModifier:
            original_mode = self.plugin.selection_mode
            self.plugin.set_selection_mode(SelectionMode.SUBTRACT)
        elif modifiers == (Qt.ControlModifier | Qt.ShiftModifier):
            original_mode = self.plugin.selection_mode
            self.plugin.set_selection_mode(SelectionMode.INTERSECT)
        else:
            original_mode = None

        point = self.toMapCoordinates(event.pos())
        mask = self.plugin.apply_magic_wand(point)
        
        # 恢复原始模式（如果使用了修饰键临时改变）
        if original_mode is not None:
            self.plugin.set_selection_mode(original_mode)
        
        if mask is not None:
            try:
                self.refresh_display()
            except Exception as exc:
                # The selection itself is already stored.  Keep the plugin
                # usable and write the full rendering traceback to the QGIS
                # log instead of raising a generic Python error.
                QgsMessageLog.logMessage(
                    "Selection display failed:\n{}".format(traceback.format_exc()),
                    "Magic Wand",
                    Qgis.Critical
                )
                self.plugin.show_message(
                    "Selection created, but display failed: {}".format(exc),
                    Qgis.Warning
                )

    def add_polygon_vertex(self, point: QgsPointXY):
        """添加一个多边形节点并显示临时绘制轮廓。"""
        if self.polygon_preview is None:
            self.polygon_preview = QgsRubberBand(
                self.canvas, QgsWkbTypes.PolygonGeometry
            )
            outline = QColor(0, 170, 255)
            fill = QColor(0, 170, 255, 35)
            self.polygon_preview.setColor(outline)
            self.polygon_preview.setFillColor(fill)
            self.polygon_preview.setWidth(2)

        self.polygon_points.append(QgsPointXY(point))
        self.polygon_preview.addPoint(point, True)
        self.plugin.show_message(
            "Polygon vertex added: {} (right-click to finish)".format(
                len(self.polygon_points)
            )
        )

    def finish_polygon(self):
        """完成多边形绘制并提取其内部区域。"""
        if len(self.polygon_points) < 3:
            self.plugin.show_message(
                "Polygon needs at least 3 vertices", Qgis.Warning
            )
            return
        points = list(self.polygon_points)
        self.cancel_polygon()
        mask = self.plugin.apply_polygon_selection(points)
        if mask is not None:
            try:
                self.refresh_display()
            except Exception as exc:
                QgsMessageLog.logMessage(
                    "Polygon display failed:\n{}".format(traceback.format_exc()),
                    "Magic Wand",
                    Qgis.Critical
                )
                self.plugin.show_message(
                    "Polygon created, but display failed: {}".format(exc),
                    Qgis.Warning
                )

    def cancel_polygon(self):
        """取消当前尚未完成的多边形。"""
        self.polygon_points = []
        if self.polygon_preview is not None:
            try:
                self.polygon_preview.reset(QgsWkbTypes.PolygonGeometry)
                if self.polygon_preview.scene():
                    self.polygon_preview.scene().removeItem(self.polygon_preview)
            except (RuntimeError, TypeError) as e:
                QgsMessageLog.logMessage(
                    f"Failed to clear polygon preview: {e}",
                    "GeoStar Selector",
                    Qgis.Warning,
                )
            self.polygon_preview = None

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape and self.plugin.selection_method == "polygon":
            self.cancel_polygon()
            self.plugin.show_message("Polygon drawing cancelled")
            event.accept()
            return
        super().keyPressEvent(event)

    def refresh_display(self):
        """刷新显示所有选择"""
        self.clear_rubber_bands()

        layer = self.plugin.canvas.currentLayer()
        if not layer:
            return

        layer_id = layer.id()
        if layer_id not in self.plugin.layer_features:
            return

        features = self.plugin.layer_features[layer_id]
        if not features:
            return

        # 显示所有要素，而不是只显示最后一个
        for idx, feature_dict in enumerate(features):
            mask = feature_dict['mask']
            extent = feature_dict['extent']
            width = feature_dict['width']
            height = feature_dict['height']

            # 为不同的要素使用不同的颜色
            color_index = idx % len(self.colors)
            color = self.colors[color_index]

            self.display_single_selection(mask, extent, width, height, color, idx + 1)

    def display_single_selection(self, mask: np.ndarray, extent, width, height, color, feature_id):
        """显示单个选择结果"""
        if mask is None or np.sum(mask) == 0:
            return

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            if len(contour) < 3:
                continue

            # QGIS 3 expects an explicit geometry type.  Passing the legacy
            # boolean True raises a SIP TypeError on recent QGIS builds.
            rubber_band = QgsRubberBand(
                self.canvas, QgsWkbTypes.PolygonGeometry
            )

            layer = self.plugin.canvas.currentLayer()
            for point in contour:
                pt = self.plugin.pixel_to_world(point[0][0], point[0][1], extent, width, height)
                if isinstance(layer, QgsRasterLayer):
                    pt = self.plugin.layer_to_canvas_point(pt, layer)
                rubber_band.addPoint(pt, False)

            # 闭合多边形
            if len(contour) > 0:
                pt = self.plugin.pixel_to_world(contour[0][0][0], contour[0][0][1], extent, width, height)
                if isinstance(layer, QgsRasterLayer):
                    pt = self.plugin.layer_to_canvas_point(pt, layer)
                rubber_band.addPoint(pt, True)

            # 设置颜色和样式
            rubber_band.setColor(color)
            # 创建半透明填充颜色
            fill_color = QColor(color)
            fill_color.setAlpha(80)  # 稍微增加透明度，便于区分多个要素
            rubber_band.setFillColor(fill_color)
            rubber_band.setWidth(2)
            rubber_band.setLineStyle(Qt.SolidLine)
            rubber_band.show()
            self.rubber_bands.append(rubber_band)

    def display_selection(self, mask: np.ndarray, extent=None, width=None, height=None):
        """显示选择结果 - 保持兼容性的包装方法"""
        # 这个方法保持不变，用于兼容性
        if mask is None or np.sum(mask) == 0:
            return

        if extent is None:
            extent = self.plugin.canvas.extent()
        if width is None or height is None:
            settings = self.plugin.canvas.mapSettings()
            width = settings.outputSize().width()
            height = settings.outputSize().height()

        # 使用黄色作为默认颜色
        color = QColor(255, 255, 0)  # 黄色
        self.display_single_selection(mask, extent, width, height, color, 0)

    def canvasPressEvent(self, event):
        """处理鼠标按下事件，防止右键菜单"""
        if event.button() == Qt.RightButton:
            event.ignore()
            return
        super().canvasPressEvent(event)

    def clear_rubber_bands(self):
        """清除所有橡皮筋"""
        for rb in self.rubber_bands:
            try:
                rb.reset(QgsWkbTypes.PolygonGeometry)
                if rb.scene():
                    rb.scene().removeItem(rb)
            except (RuntimeError, TypeError) as e:
                QgsMessageLog.logMessage(
                    f"Failed to remove rubber band: {e}",
                    "GeoStar Selector",
                    Qgis.Warning,
                )
        self.rubber_bands.clear()
        # 刷新画布
        self.canvas.refresh()

    def cleanup(self):
        self.cancel_polygon()
        self.clear_rubber_bands()

    def deactivate(self):
        super().deactivate()
        self.plugin.deactivate_tool()
