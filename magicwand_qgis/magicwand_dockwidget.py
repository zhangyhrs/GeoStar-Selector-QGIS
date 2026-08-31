from qgis.PyQt.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QPushButton, QSpinBox, QComboBox,
    QMessageBox, QFileDialog, QGroupBox, QButtonGroup, QRadioButton,
    QCheckBox, QFrame, QSizePolicy, QToolButton, QScrollArea
)
from qgis.PyQt.QtCore import Qt, pyqtSignal, QPropertyAnimation, QRect, QEasingCurve
from qgis.PyQt.QtGui import QFont, QIcon, QPalette, QPixmap
from qgis.core import QgsProject, QgsMapLayer, QgsVectorFileWriter
from .magicwand import SelectionMode
import numpy as np
import cv2
import os


class CollapsibleGroupBox(QGroupBox):
    """可折叠的组框"""

    def __init__(self, title="", parent=None):
        super().__init__(title, parent)
        self.setCheckable(True)
        self.setChecked(True)  # 默认展开

        # 连接点击事件
        self.clicked.connect(self.toggle_content)

        # 设置样式
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #CCCCCC;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #333333;
            }
            QGroupBox::indicator {
                width: 13px;
                height: 13px;
                margin-left: 2px;
            }
            QGroupBox::indicator:unchecked {
                image: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA0AAAANCAYAAAA8R9KVAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAAdgAAAHYBTnsmCAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAFYSURBVCiRpZM9SwNBEIafgwQLwcJCG1sLwcJCG1sLwUKwsLBQsLCwULCwsLBQsLCwsLBQsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQ);
            }
            QGroupBox::indicator:checked {
                image: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA0AAAANCAYAAAA8R9KVAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAAdgAAAHYBTnsmCAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAFYSURBVCiRpZM9SwNBEIafgwQLwcJCG1sLwcJCG1sLwUKwsLBQsLCwULCwsLBQsLCwsLBQsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQ);
            }
        """)

        self.content_widget = None
        self.animation = None

    def setContentLayout(self, content_layout):
        """设置内容布局"""
        # 创建内容容器
        self.content_widget = QWidget()
        self.content_widget.setLayout(content_layout)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 20, 5, 5)
        main_layout.addWidget(self.content_widget)

        # 创建动画
        self.animation = QPropertyAnimation(self.content_widget, b"maximumHeight")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.InOutQuart)

    def toggle_content(self, checked):
        """切换内容显示/隐藏"""
        if not self.content_widget or not self.animation:
            return

        if checked:
            # 展开
            self.content_widget.setMaximumHeight(16777215)  # 移除高度限制
            self.animation.setStartValue(0)
            self.animation.setEndValue(self.content_widget.sizeHint().height())
        else:
            # 折叠
            self.animation.setStartValue(self.content_widget.height())
            self.animation.setEndValue(0)

        self.animation.finished.connect(lambda: self._animation_finished(checked))
        self.animation.start()

    def _animation_finished(self, expanded):
        """动画完成后的处理"""
        if not expanded:
            self.content_widget.setMaximumHeight(0)
        else:
            self.content_widget.setMaximumHeight(16777215)


class MagicWandDockWidget(QDockWidget):
    # 定义信号
    selection_mode_changed = pyqtSignal(SelectionMode)

    def __init__(self, plugin, parent=None):
        super().__init__("魔法棒管理器", parent)
        self.plugin = plugin
        self.setObjectName("MagicWandDockWidget")
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        # 设置窗口图标
        self.setup_window_icon()

        # 创建自定义标题栏
        self.setup_custom_title()

        # 创建主容器和滚动区域
        main_container = QWidget()
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 添加自定义标题栏
        main_layout.addWidget(self.title_widget)

        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        self.layout = QVBoxLayout(scroll_widget)
        self.layout.setSpacing(8)
        self.layout.setContentsMargins(5, 5, 5, 5)

        # 创建各个组件
        self.create_selection_method_group()
        self.create_selection_mode_group()
        self.create_layer_selection_group()
        self.create_parameters_group()
        self.create_shortcuts_group()
        self.create_export_group()
        self.create_clear_operations_group()
        self.create_help_group()

        # 添加弹性空间
        self.layout.addStretch()

        # 设置滚动区域
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # 添加滚动区域到主布局
        main_layout.addWidget(scroll_area)

        self.setWidget(main_container)
        self.setMinimumWidth(300)
        self.setMaximumWidth(400)

        # 设置整体样式 - 移除原始标题栏
        self.setStyleSheet("""
            QDockWidget {
                font-size: 11px;
                titlebar-close-icon: none;
                titlebar-normal-icon: none;
            }
            QDockWidget::title {
                background: transparent;
                text-align: left;
                padding: 0px;
                margin: 0px;
                border: none;
            }
        """)

        # 隐藏原始标题栏
        self.setTitleBarWidget(QWidget())

        # 初始化更新
        self.update_feature_count()

    def setup_window_icon(self):
        """设置窗口图标"""
        try:
            # 获取插件目录路径
            plugin_dir = os.path.dirname(os.path.realpath(__file__))
            icon_path = os.path.join(plugin_dir, "logo.png")

            if os.path.exists(icon_path):
                icon = QIcon(icon_path)
                self.setWindowIcon(icon)
            else:
                # 如果icon.png不存在，使用默认图标
                self.setWindowIcon(self.style().standardIcon(self.style().SP_ComputerIcon))
        except Exception as e:
            # 出错时使用默认图标
            self.setWindowIcon(self.style().standardIcon(self.style().SP_ComputerIcon))

    def setup_custom_title(self):
        """创建自定义标题栏"""
        self.title_widget = QWidget()
        self.title_widget.setFixedHeight(35)
        self.title_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #4A90E2, stop: 1 #357ABD);
                border: 1px solid #2E5C8A;
                border-radius: 0px;
            }
        """)

        title_layout = QHBoxLayout(self.title_widget)
        title_layout.setContentsMargins(8, 2, 8, 2)
        title_layout.setSpacing(8)

        # Logo图标
        self.logo_label = QLabel()
        self.setup_logo()
        title_layout.addWidget(self.logo_label)

        # 标题文本
        title_label = QLabel("GeoStar Selector")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-weight: bold;
                font-size: 12px;
                background: transparent;
                border: none;
            }
        """)
        title_layout.addWidget(title_label)

        # 添加弹性空间，将控制按钮推到右边
        title_layout.addStretch()

        # 最小化按钮
        self.minimize_btn = QPushButton("−")
        self.minimize_btn.setFixedSize(20, 20)
        self.minimize_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 3px;
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        self.minimize_btn.clicked.connect(self.toggle_minimize)
        title_layout.addWidget(self.minimize_btn)

        # 关闭按钮
        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(20, 20)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 0, 0, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 3px;
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(255, 0, 0, 0.5);
            }
            QPushButton:pressed {
                background-color: rgba(255, 0, 0, 0.7);
            }
        """)
        self.close_btn.clicked.connect(self.close)
        title_layout.addWidget(self.close_btn)

        # 存储最小化状态
        self.is_minimized = False

    def setup_logo(self):
        """设置Logo图标"""
        try:
            # 获取插件目录路径
            plugin_dir = os.path.dirname(os.path.realpath(__file__))
            logo_path = os.path.join(plugin_dir, "logo.png")

            if os.path.exists(logo_path):
                # 加载并缩放logo
                pixmap = QPixmap(logo_path)
                if not pixmap.isNull():
                    # 缩放到合适大小，保持宽高比
                    scaled_pixmap = pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.logo_label.setPixmap(scaled_pixmap)
                else:
                    self.setup_default_logo()
            else:
                self.setup_default_logo()

        except Exception as e:
            self.setup_default_logo()

    def setup_default_logo(self):
        """设置默认Logo图标"""
        self.logo_label.setText("🪄")  # 使用魔法棒emoji作为默认图标
        self.logo_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 18px;
                background: transparent;
                border: none;
            }
        """)
        self.logo_label.setFixedSize(24, 24)
        self.logo_label.setAlignment(Qt.AlignCenter)

    def toggle_minimize(self):
        """切换最小化状态"""
        if self.is_minimized:
            # 展开
            self.widget().show()
            self.minimize_btn.setText("−")
            self.is_minimized = False
            self.setFixedHeight(self.sizeHint().height())
        else:
            # 最小化
            self.widget().hide()
            self.minimize_btn.setText("+")
            self.is_minimized = True
            self.setFixedHeight(self.title_widget.height())

    def create_selection_mode_group(self):
        """创建选择模式组"""
        mode_group = CollapsibleGroupBox("选择模式")
        mode_layout = QVBoxLayout()

        # 当前模式显示
        self.current_mode_label = QLabel("当前模式：新建要素")
        font = QFont()
        font.setBold(True)
        self.current_mode_label.setFont(font)
        self.current_mode_label.setStyleSheet("""
            QLabel { 
                color: #2E7D32; 
                background-color: #E8F5E8;
                padding: 5px;
                border-radius: 3px;
                border: 1px solid #C8E6C9;
            }
        """)
        mode_layout.addWidget(self.current_mode_label)

        # 添加分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("QFrame { color: #CCCCCC; }")
        mode_layout.addWidget(line)

        # 模式选择按钮
        buttons_layout = QVBoxLayout()
        self.mode_group = QButtonGroup()

        self.new_radio = QRadioButton("新建要素 (W)")
        self.add_radio = QRadioButton("添加到最后要素 (Shift+W)")
        self.subtract_radio = QRadioButton("从最后要素减去 (Alt+W)")
        self.intersect_radio = QRadioButton("与最后要素相交 (Ctrl+Shift+W)")

        # 设置单选按钮样式
        radio_style = """
            QRadioButton {
                padding: 3px;
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 15px;
                height: 15px;
            }
            QRadioButton:disabled {
                color: #888888;
            }
        """

        for radio in [self.new_radio, self.add_radio, self.subtract_radio, self.intersect_radio]:
            radio.setStyleSheet(radio_style)

        self.new_radio.setChecked(True)  # 默认选择新建

        self.mode_group.addButton(self.new_radio, 0)
        self.mode_group.addButton(self.add_radio, 1)
        self.mode_group.addButton(self.subtract_radio, 2)
        self.mode_group.addButton(self.intersect_radio, 3)

        buttons_layout.addWidget(self.new_radio)
        buttons_layout.addWidget(self.add_radio)
        buttons_layout.addWidget(self.subtract_radio)
        buttons_layout.addWidget(self.intersect_radio)

        mode_layout.addLayout(buttons_layout)

        # 连接信号
        self.mode_group.buttonClicked.connect(self.on_mode_changed)

        mode_group.setContentLayout(mode_layout)
        self.layout.addWidget(mode_group)

    def create_selection_method_group(self):
        """创建魔术棒/多边形提取方式切换组。"""
        method_group_box = CollapsibleGroupBox("提取方式")
        method_layout = QVBoxLayout()

        self.method_group = QButtonGroup()
        self.magic_wand_radio = QRadioButton("魔术棒：单击相似连续区域")
        self.polygon_radio = QRadioButton("多边形：左键绘制，右键完成")
        self.magic_wand_radio.setChecked(True)
        self.method_group.addButton(self.magic_wand_radio, 0)
        self.method_group.addButton(self.polygon_radio, 1)
        method_layout.addWidget(self.magic_wand_radio)
        method_layout.addWidget(self.polygon_radio)

        method_tip = QLabel("多边形模式：左键添加节点，右键完成，Esc取消。")
        method_tip.setWordWrap(True)
        method_tip.setStyleSheet("QLabel { color: #666; padding: 4px; }")
        method_layout.addWidget(method_tip)

        self.method_group.buttonClicked.connect(self.on_method_changed)
        method_group_box.setContentLayout(method_layout)
        self.layout.addWidget(method_group_box)

    def create_layer_selection_group(self):
        """创建图层选择组"""
        layer_group = CollapsibleGroupBox("图层选择")
        layer_layout = QVBoxLayout()

        layer_layout.addWidget(QLabel("当前图层："))
        self.layer_list = QComboBox()
        self.layer_list.setStyleSheet("""
            QComboBox {
                padding: 5px;
                border: 1px solid #CCCCCC;
                border-radius: 3px;
                background-color: white;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
            }
        """)
        self.refresh_layers()
        self.layer_list.currentTextChanged.connect(self.on_layer_changed)
        layer_layout.addWidget(self.layer_list)

        # 统计信息容器
        stats_widget = QWidget()
        stats_widget.setStyleSheet("""
            QWidget {
                background-color: #F5F5F5;
                border: 1px solid #E0E0E0;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        stats_layout = QVBoxLayout(stats_widget)
        stats_layout.setContentsMargins(8, 8, 8, 8)

        # 当前图层要素数量显示
        self.selection_label = QLabel("要素数量：0")
        self.selection_label.setStyleSheet("QLabel { font-weight: bold; color: #1976D2; }")
        stats_layout.addWidget(self.selection_label)

        # 总要素数量显示
        self.total_label = QLabel("总要素数量：0")
        self.total_label.setStyleSheet("QLabel { color: #666666; }")
        stats_layout.addWidget(self.total_label)

        layer_layout.addWidget(stats_widget)

        layer_group.setContentLayout(layer_layout)
        self.layout.addWidget(layer_group)

    def create_parameters_group(self):
        """创建参数设置组"""
        params_group = CollapsibleGroupBox("参数设置")
        params_layout = QVBoxLayout()

        # 容差设置
        tolerance_layout = QHBoxLayout()
        tolerance_layout.addWidget(QLabel("容差："))

        self.btn_tolerance_down = QPushButton("-")
        self.btn_tolerance_up = QPushButton("+")

        button_style = """
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: bold;
                min-width: 25px;
                max-width: 25px;
                min-height: 25px;
                max-height: 25px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """

        self.btn_tolerance_down.setStyleSheet(button_style)
        self.btn_tolerance_up.setStyleSheet(button_style)
        self.btn_tolerance_down.clicked.connect(self.plugin.decrease_tolerance)
        self.btn_tolerance_up.clicked.connect(self.plugin.increase_tolerance)

        self.tolerance_spin = QSpinBox()
        self.tolerance_spin.setRange(1, 100)
        self.tolerance_spin.setValue(self.plugin.tolerance)
        self.tolerance_spin.valueChanged.connect(self.plugin.set_tolerance)
        self.tolerance_spin.setStyleSheet("""
            QSpinBox {
                padding: 5px;
                border: 1px solid #CCCCCC;
                border-radius: 3px;
                background-color: white;
                font-weight: bold;
                text-align: center;
            }
        """)

        shortcut_label = QLabel("(Ctrl+/-)")
        shortcut_label.setStyleSheet("QLabel { color: #666666; font-size: 9px; }")

        tolerance_layout.addWidget(self.btn_tolerance_down)
        tolerance_layout.addWidget(self.tolerance_spin)
        tolerance_layout.addWidget(self.btn_tolerance_up)
        tolerance_layout.addWidget(shortcut_label)
        params_layout.addLayout(tolerance_layout)

        # 连通性设置
        connectivity_layout = QVBoxLayout()
        connectivity_layout.addWidget(QLabel("连通性："))
        self.connectivity_combo = QComboBox()
        self.connectivity_combo.addItems(["4连通", "8连通"])
        self.connectivity_combo.setCurrentIndex(0 if self.plugin.connectivity == 4 else 1)
        self.connectivity_combo.currentIndexChanged.connect(
            lambda: self.plugin.set_connectivity(4 if self.connectivity_combo.currentIndex() == 0 else 8)
        )
        self.connectivity_combo.setStyleSheet("""
            QComboBox {
                padding: 5px;
                border: 1px solid #CCCCCC;
                border-radius: 3px;
                background-color: white;
            }
        """)
        connectivity_layout.addWidget(self.connectivity_combo)
        params_layout.addLayout(connectivity_layout)

        params_group.setContentLayout(params_layout)
        self.layout.addWidget(params_group)

    def create_shortcuts_group(self):
        """创建快捷操作组"""
        shortcuts_group = CollapsibleGroupBox("快捷操作")
        shortcuts_group.setChecked(False)  # 默认折叠
        shortcuts_layout = QVBoxLayout()

        # 撤销按钮
        self.btn_undo = QPushButton("撤销最后选择 (Ctrl+Z)")
        self.btn_undo.clicked.connect(self.plugin.undo_last_selection)
        self.btn_undo.setStyleSheet("""
            QPushButton { 
                background-color: #FF9800; 
                color: white; 
                border: none;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
                color: #666666;
            }
        """)
        shortcuts_layout.addWidget(self.btn_undo)

        # 快捷键说明
        shortcuts_text = QLabel("""<b>键盘快捷键：</b><br>
• W: 激活魔法棒工具<br>
• Shift+点击: 添加到最后要素<br>
• Alt+点击: 从最后要素减去<br>
• Ctrl+Shift+点击: 与最后要素相交<br>
• Ctrl++/-: 调整容差<br>
• Delete: 清除当前图层<br>
• Ctrl+Delete: 清除所有<br>
• Ctrl+Z: 撤销最后选择<br><br>
<b>要素模式：</b><br>
• 每次"新建要素"点击创建独立选择<br>
• 所有要素都会保留并以不同颜色显示<br>
• 修改模式只影响最近创建的要素""")
        shortcuts_text.setWordWrap(True)
        shortcuts_text.setStyleSheet("""
            QLabel { 
                color: #424242; 
                font-size: 12px;
                background-color: #F9F9F9;
                padding: 8px;
                border: 1px solid #E0E0E0;
                border-radius: 5px;
            }
        """)
        shortcuts_layout.addWidget(shortcuts_text)

        shortcuts_group.setContentLayout(shortcuts_layout)
        self.layout.addWidget(shortcuts_group)

    def create_export_group(self):
        """创建导出设置组"""
        export_group = CollapsibleGroupBox("导出选项")
        export_layout = QVBoxLayout()

        # 导出格式选择
        format_layout = QHBoxLayout()
        self.format_group = QButtonGroup()

        self.shp_radio = QRadioButton("Shapefile (.shp)")
        self.json_radio = QRadioButton("GeoJSON (.json)")
        self.shp_radio.setChecked(True)  # 默认选择SHP

        # 设置样式
        format_style = """
            QRadioButton {
                padding: 5px;
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 15px;
                height: 15px;
            }
        """
        self.shp_radio.setStyleSheet(format_style)
        self.json_radio.setStyleSheet(format_style)

        self.format_group.addButton(self.shp_radio, 0)
        self.format_group.addButton(self.json_radio, 1)

        format_layout.addWidget(self.shp_radio)
        format_layout.addWidget(self.json_radio)
        export_layout.addLayout(format_layout)

        # 导出按钮
        self.btn_export = QPushButton("导出所有要素")
        self.btn_export.clicked.connect(self.export_features)
        self.btn_export.setStyleSheet("""
            QPushButton { 
                background-color: #4CAF50; 
                color: white; 
                font-weight: bold;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
                color: #666666;
            }
        """)
        export_layout.addWidget(self.btn_export)

        export_group.setContentLayout(export_layout)
        self.layout.addWidget(export_group)

    def create_clear_operations_group(self):
        """创建清除操作组"""
        clear_group = CollapsibleGroupBox("清除操作")
        clear_layout = QVBoxLayout()

        self.btn_clear_current = QPushButton("清除当前图层 (Delete)")
        self.btn_clear_current.clicked.connect(self.plugin.clear_current_selection)
        self.btn_clear_current.setStyleSheet("""
            QPushButton {
                background-color: #FFC107;
                color: #333333;
                border: none;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FFB300;
            }
        """)
        clear_layout.addWidget(self.btn_clear_current)

        self.btn_clear_all = QPushButton("清除所有要素 (Ctrl+Delete)")
        self.btn_clear_all.clicked.connect(self.plugin.clear_all_selections)
        self.btn_clear_all.setStyleSheet("""
            QPushButton { 
                background-color: #f44336; 
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
        """)
        clear_layout.addWidget(self.btn_clear_all)

        clear_group.setContentLayout(clear_layout)
        self.layout.addWidget(clear_group)

    def create_help_group(self):
        """创建使用说明组"""
        help_group = CollapsibleGroupBox("使用说明")
        help_group.setChecked(False)  # 默认折叠
        help_layout = QVBoxLayout()

        help_text = QLabel("""<b>使用方法：</b><br>
1. 从列表中选择栅格图层<br>
2. 使用"新建要素"模式创建独立选择<br>
3. 每次点击创建独立要素（不同颜色显示）<br>
4. 使用"添加/减去/相交"修改最后一个要素<br>
5. 根据需要调整容差和连通性<br>
6. 准备好后导出所有要素<br><br>
<b>使用技巧：</b><br>
• 所有要素都会保留直到手动清除<br>
• 不同颜色帮助区分多个要素<br>
• 非常适合选择多个分散区域""")
        help_text.setWordWrap(True)
        help_text.setStyleSheet("""
            QLabel { 
                color: #666; 
                font-size: 12px;
                background-color: #F9F9F9;
                padding: 8px;
                border: 1px solid #E0E0E0;
                border-radius: 5px;
                line-height: 1.4;
            }
        """)
        help_layout.addWidget(help_text)

        help_group.setContentLayout(help_layout)
        self.layout.addWidget(help_group)

    def on_mode_changed(self, button):
        """选择模式改变时的处理"""
        mode_map = {
            self.new_radio: SelectionMode.NEW,
            self.add_radio: SelectionMode.ADD,
            self.subtract_radio: SelectionMode.SUBTRACT,
            self.intersect_radio: SelectionMode.INTERSECT
        }

        mode = mode_map.get(button)
        if mode:
            self.plugin.set_selection_mode(mode)
            self.update_selection_mode_display(mode)

    def on_method_changed(self, button):
        """提取方式改变时的处理。"""
        method = "polygon" if button is self.polygon_radio else "magic_wand"
        self.plugin.set_selection_method(method)

    def update_selection_mode(self, mode: SelectionMode):
        """更新选择模式显示"""
        mode_buttons = {
            SelectionMode.NEW: self.new_radio,
            SelectionMode.ADD: self.add_radio,
            SelectionMode.SUBTRACT: self.subtract_radio,
            SelectionMode.INTERSECT: self.intersect_radio
        }

        button = mode_buttons.get(mode)
        if button:
            button.setChecked(True)

        self.update_selection_mode_display(mode)

    def update_selection_mode_display(self, mode: SelectionMode):
        """更新当前模式显示标签"""
        mode_text = {
            SelectionMode.NEW: "新建要素",
            SelectionMode.ADD: "添加到最后要素",
            SelectionMode.SUBTRACT: "从最后要素减去",
            SelectionMode.INTERSECT: "与最后要素相交"
        }

        mode_colors = {
            SelectionMode.NEW: "#2E7D32",  # 绿色
            SelectionMode.ADD: "#1976D2",  # 蓝色
            SelectionMode.SUBTRACT: "#D32F2F",  # 红色
            SelectionMode.INTERSECT: "#F57C00"  # 橙色
        }

        mode_backgrounds = {
            SelectionMode.NEW: "#E8F5E8",
            SelectionMode.ADD: "#E3F2FD",
            SelectionMode.SUBTRACT: "#FFEBEE",
            SelectionMode.INTERSECT: "#FFF3E0"
        }

        text = mode_text.get(mode, "未知模式")
        color = mode_colors.get(mode, "#000000")
        bg_color = mode_backgrounds.get(mode, "#F5F5F5")

        self.current_mode_label.setText("当前模式：{}".format(text))
        self.current_mode_label.setStyleSheet("""
            QLabel {{ 
                color: {}; 
                background-color: {};
                padding: 5px;
                border-radius: 3px;
                border: 1px solid {};
                font-weight: bold;
            }}
        """.format(color, bg_color, color))

    def refresh_layers(self):
        """刷新图层列表"""
        current_text = self.layer_list.currentText()
        self.layer_list.clear()

        raster_layers = []
        for layer in QgsProject.instance().mapLayers().values():
            if layer.type() == QgsMapLayer.RasterLayer:
                raster_layers.append((layer.name(), layer.id()))

        if not raster_layers:
            self.layer_list.addItem("无栅格图层", None)
            return

        for name, layer_id in raster_layers:
            self.layer_list.addItem(name, layer_id)

        # 尝试恢复之前选择的图层
        index = self.layer_list.findText(current_text)
        if index >= 0:
            self.layer_list.setCurrentIndex(index)

    def on_layer_changed(self):
        """图层改变时更新要素计数"""
        layer_id = self.layer_list.currentData()
        layer = QgsProject.instance().mapLayer(layer_id) if layer_id else None
        if layer and layer.type() == QgsMapLayer.RasterLayer:
            self.plugin.iface.setActiveLayer(layer)
            self.plugin.clear_cached_data()
        self.update_feature_count()

    def update_feature_count(self):
        """更新要素数量显示"""
        layer_id = self.layer_list.currentData()
        if layer_id:
            current_count = len(self.plugin.layer_features.get(layer_id, []))
            self.selection_label.setText("要素数量：{}".format(current_count))
        else:
            self.selection_label.setText("要素数量：0")

        # 更新总数
        total_count = sum(len(features) for features in self.plugin.layer_features.values())
        self.total_label.setText("总要素数量：{}".format(total_count))

        # 更新按钮状态
        self.btn_export.setEnabled(total_count > 0)
        self.btn_undo.setEnabled(total_count > 0)

        # 根据是否有要素来启用/禁用某些模式
        has_features = total_count > 0
        if layer_id:
            layer_has_features = len(self.plugin.layer_features.get(layer_id, [])) > 0
            self.add_radio.setEnabled(layer_has_features)
            self.subtract_radio.setEnabled(layer_has_features)
            self.intersect_radio.setEnabled(layer_has_features)
        else:
            self.add_radio.setEnabled(False)
            self.subtract_radio.setEnabled(False)
            self.intersect_radio.setEnabled(False)

    def export_features(self):
        """导出要素"""
        if not self.plugin.layer_features:
            QMessageBox.warning(self, "警告", "没有要素可导出！")
            return

        # 获取选择的导出格式
        if self.shp_radio.isChecked():
            export_format = 'shp'
        else:
            export_format = 'json'

        # 调用插件的导出方法
        self.plugin.export_selections(export_format)

    def closeEvent(self, event):
        """面板关闭时的处理"""
        # 可以在这里添加清理代码
        event.accept()
