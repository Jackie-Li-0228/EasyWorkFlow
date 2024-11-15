import sys
import keyboard  # Import the keyboard library for global hotkeys
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QVBoxLayout, QPushButton, QWidget, QMessageBox, QLabel, QMenu, QLineEdit
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QRect, QRectF
from task_tree import TaskTree
import json
import os
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont, QPixmap, QRegion, QPainterPath
from PyQt5.QtWidgets import QGraphicsDropShadowEffect, QGraphicsOpacityEffect

class TaskManagerUI(QMainWindow):
    update_ui_signal = pyqtSignal()  # 用于更新UI显示
    task_changed_signal = pyqtSignal()  # 用于通知任务切换

    def __init__(self, task_tree):
        super().__init__()
        self.task_tree = task_tree
        self.initUI()
        self.update_ui_signal.connect(self.update_ui)
        self.task_changed_signal.connect(self.update_task_display)
        self.setup_global_hotkeys()

    def initUI(self):
        self.setWindowTitle("EasyWorkflow")
        self.setGeometry(300, 300, 600, 400)

        # 添加任务按钮
        add_task_action = QAction(QIcon(None), '添加任务', self)
        add_task_action.triggered.connect(self.add_task)

        # 完成任务按钮
        complete_task_action = QAction(QIcon(None), '完成任务', self)
        complete_task_action.triggered.connect(self.complete_task)

        # 设置工具栏
        toolbar = self.addToolBar("Main Toolbar")
        toolbar.addAction(add_task_action)
        toolbar.addAction(complete_task_action)

        # 主布局
        central_widget = QWidget(self)
        layout = QVBoxLayout(central_widget)

        # 添加按钮到布局
        add_task_btn = QPushButton("添加新任务", self)
        add_task_btn.clicked.connect(self.add_task)
        
        complete_task_btn = QPushButton("完成当前任务", self)
        complete_task_btn.clicked.connect(self.complete_task)

        mini_mode_btn = QPushButton("进入MINI模式", self)
        mini_mode_btn.clicked.connect(self.enter_mini_mode)
        
        # 新增的按钮
        new_workflow_btn = QPushButton("创建一个新的工作流", self)
        new_workflow_btn.clicked.connect(self.create_new_workflow)
        
        layout.addWidget(add_task_btn)
        layout.addWidget(complete_task_btn)
        layout.addWidget(mini_mode_btn)
        layout.addWidget(new_workflow_btn)  # 添加新按钮到布局
        
        self.setCentralWidget(central_widget)

    def setup_global_hotkeys(self):
        """设置全局快捷键"""
        keyboard.add_hotkey('ctrl+shift+alt+l', self.add_task)
        keyboard.add_hotkey('ctrl+shift+alt+k', self.rename_task)
        keyboard.add_hotkey('ctrl+shift+alt+j', self.complete_task)

    @pyqtSlot()
    def update_ui(self):
        """刷新界面显示"""
        print("UI 已更新")
        
    def add_task(self):
        """增加任务并刷新 UI"""
        task_name = "新任务"
        self.task_tree.add_task(task_name)
        print(f"任务 '{task_name}' 已添加。")
        self.update_ui_signal.emit()  # 触发 UI 更新
        self.task_changed_signal.emit()  # 通知任务切换
        self.task_tree.save_to_file()

    def rename_task(self):
        """重命名当前任务"""
        if hasattr(self, 'mini_mode_window') and self.mini_mode_window.isVisible():
            self.mini_mode_window.enter_rename_mode()
        else:
            new_name = "重命名任务"  # 这里可以弹出一个对话框获取用户输入
            self.task_tree.rename_task(new_name)
            print(f"任务已重命名为 '{new_name}'。")
            self.update_ui_signal.emit()  # 触发 UI 更新
            self.task_changed_signal.emit()  # 通知任务切换
            self.task_tree.save_to_file()

    def complete_task(self):
        """完成任务并检查是否根节点"""
        if self.task_tree.current_task == self.task_tree.root:
            print("警告: 根节点不可完成。")
            return
        self.task_tree.complete_task()
        print("任务已完成。")
        self.update_ui_signal.emit()  # 触发 UI 更新
        self.task_changed_signal.emit()  # 通知任务切换
        self.task_tree.save_to_file()

    def enter_mini_mode(self):
        self.mini_mode_window = MiniModeWindow(self)
        self.mini_mode_window.show()
        self.hide()

    def update_task_display(self):
        """更新任务显示"""
        if hasattr(self, 'mini_mode_window') and self.mini_mode_window.isVisible():
            self.mini_mode_window.update_task_name()

    def create_new_workflow(self):
        """创建一个新的工作流"""
        self.task_tree.reset_to_root()  # 假设有一个方法可以重置 task_tree
        print("新的工作流已创建。")
        self.update_ui_signal.emit()  # 触发 UI 更新
        self.task_changed_signal.emit()  # 通知任务切换
        self.task_tree.save_to_file()

class MiniModeWindow(QMainWindow):
    CONFIG_FILE = "mini_mode_config.json"

    def __init__(self, task_manager_ui):
        super().__init__()
        self.task_manager_ui = task_manager_ui
        self.config = self.load_config()
        self.initUI()
        self.offset = None  # 添加这一行，初始化 offset 属性

        # 连接信号
        self.task_manager_ui.update_ui_signal.connect(self.update_task_name)
        self.task_manager_ui.task_changed_signal.connect(self.update_task_name)

    def initUI(self):
        # 设置窗口标志
        flags = Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        if self.config["window"].get("resizable", False):
            flags |= Qt.Window
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        # 设置窗口几何信息
        position = self.config.get("position", {})
        self.setGeometry(
            position.get("x", 100),
            position.get("y", 100),
            position.get("width", 200),
            position.get("height", 100)
        )

        # 设置样式
        self.setStyleSheet(f"""
            background-color: {self.config["window"]["background"]["color"]};
            border-radius: {self.config["window"]["border_radius"]}px;
        """)

        # 设置阴影效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 0)

        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFont(QFont(self.config["font"]["family"], self.config["font"]["size"]))
        self.update_task_name()

        self.input_field = QLineEdit(self)
        self.input_field.setAlignment(Qt.AlignCenter)
        self.input_field.hide()
        self.input_field.returnPressed.connect(self.rename_task)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.input_field)

        central_widget = QWidget(self)
        central_widget.setLayout(layout)
        central_widget.setGraphicsEffect(shadow)
        
        # 应用背景样式
        self.apply_background_style(central_widget)
        self.setCentralWidget(central_widget)

        # 设置圆角遮罩
        self.set_rounded_corners()

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def set_rounded_corners(self):
        """设置圆角遮罩"""
        radius = self.config["window"]["border_radius"]
        path = QPainterPath()
        rect = QRectF(0, 0, self.width(), self.height())
        path.addRoundedRect(rect, radius, radius)
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)

    def update_task_name(self):
        """更新任务名称并调整窗口宽度"""
        task_name = self.task_manager_ui.task_tree.current_task.name
        self.label.setText(task_name)
        self.adjust_window_width()

    def adjust_window_width(self):
        """根据标签内容自动调整窗口宽度"""
        # 获取文本的宽度
        text_width = self.label.fontMetrics().boundingRect(self.label.text()).width()
        # 设置窗口宽度，增加一些边距
        new_width = text_width + 40  # 40 是一个经验值，可以根据需要调整
        self.setFixedWidth(new_width)
        self.set_rounded_corners()  # 更新圆角遮罩

    def show_context_menu(self, pos):
        context_menu = QMenu(self)

        toggle_top_action = QAction("切换置顶", self)
        toggle_top_action.triggered.connect(self.toggle_always_on_top)
        context_menu.addAction(toggle_top_action)

        # 预留更多操作
        # context_menu.addAction(QAction("其他操作", self))

        context_menu.exec_(self.mapToGlobal(pos))

    def toggle_always_on_top(self):
        if self.windowFlags() & Qt.WindowStaysOnTopHint:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.show()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.offset is not None:
            self.move(self.pos() + event.pos() - self.offset)

    def mouseReleaseEvent(self, event):
        self.offset = None

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.task_manager_ui.show()
            self.close()

    def enter_rename_mode(self):
        """进入重命名模式"""
        current_task_name = self.task_manager_ui.task_tree.current_task.name
        self.label.hide()
        self.input_field.setText(current_task_name)  # 使用当前任务名称
        self.input_field.setGeometry(self.label.geometry())  # 设置输入框位置和大小
        self.input_field.show()
        self.input_field.setFocus()
        self.input_field.selectAll()  # 选中所有文本方便编辑

    def rename_task(self):
        """重命名任务并调整窗口宽度"""
        new_name = self.input_field.text().strip()
        if new_name:
            self.task_manager_ui.task_tree.rename_task(new_name)
            self.task_manager_ui.task_tree.save_to_file()  # 保存更改
            self.task_manager_ui.update_ui_signal.emit()
            self.task_manager_ui.task_changed_signal.emit()
        
        self.input_field.hide()
        self.label.show()
        self.update_task_name()

    def load_config(self):
        default_config = {
            "window": {
                "background": {
                    "type": "color",
                    "color": "#FFFFFF",
                    "image_path": "background.png",
                    "size": "cover",
                    "position": "center",
                    "repeat": "no-repeat"
                },
                "border_radius": 15,
                "resizable": True
            },
            "font": {
                "family": "Arial",
                "size": 12
            },
            "animations": {
                "task_created": "",
                "task_completed": ""
            },
            "position": {
                "x": 100,
                "y": 100,
                "width": 200,
                "height": 50
            }
        }

        if os.path.exists(self.CONFIG_FILE):
            with open(self.CONFIG_FILE, 'r') as file:
                try:
                    config = json.load(file)
                    # 合并默认配置和文件配置
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                        elif isinstance(value, dict):
                            for sub_key, sub_value in value.items():
                                if sub_key not in config[key]:
                                    config[key][sub_key] = sub_value
                    return config
                except json.JSONDecodeError:
                    print("JSON 文件格式错误，使用默认配置。")
        else:
            print("配置文件不存在，使用默认配置。")

        return default_config

    def save_config(self):
        # 更新配置中的位置信息
        self.config["position"] = {
            "x": self.x(),
            "y": self.y(),
            "width": self.width(),
            "height": self.height()
        }
        with open(self.CONFIG_FILE, 'w') as file:
            json.dump(self.config, file, indent=4)

    def moveEvent(self, event):
        """在窗口移动时检查并调整位置"""
        self.ensure_not_covered_by_taskbar()
        self.save_config()
        super().moveEvent(event)

    def ensure_not_covered_by_taskbar(self):
        """确保窗口不被任务栏遮挡"""
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        window_geometry = self.geometry()

        # 检查并调整窗口位置
        new_x = window_geometry.x()
        new_y = window_geometry.y()

        if window_geometry.bottom() > screen_geometry.bottom():
            new_y = screen_geometry.bottom() - window_geometry.height()
        if window_geometry.right() > screen_geometry.right():
            new_x = screen_geometry.right() - window_geometry.width()
        if window_geometry.top() < screen_geometry.top():
            new_y = screen_geometry.top()
        if window_geometry.left() < screen_geometry.left():
            new_x = screen_geometry.left()

        if new_x != window_geometry.x() or new_y != window_geometry.y():
            self.move(new_x, new_y)

    def resizeEvent(self, event):
        """在窗口大小调整时保存配置"""
        self.save_config()
        super().resizeEvent(event)

    def closeEvent(self, event):
        self.save_config()
        super().closeEvent(event)

    def play_animation(self, animation_type):
        animation_path = self.config["animations"].get(animation_type, "")
        if animation_path and os.path.exists(animation_path):
            # 这里可以实现播放动画的逻辑，例如使用 QLabel 显示 GIF
            pass

    def showEvent(self, event):
        super().showEvent(event)
        self.adjust_position()

    def adjust_position(self):
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        window_geometry = self.geometry()

        # 检查窗口是否超出屏幕可用区域
        if window_geometry.bottom() > screen_geometry.bottom():
            self.move(window_geometry.x(), screen_geometry.bottom() - window_geometry.height())
        if window_geometry.right() > screen_geometry.right():
            self.move(screen_geometry.right() - window_geometry.width(), window_geometry.y())

    def apply_background_style(self, widget):
        """应用背景样式"""
        background_config = self.config["window"]["background"]
        style = f"border-radius: {self.config['window']['border_radius']}px;"
        
        if background_config["type"] == "color":
            # 纯色背景
            style += f"background-color: {background_config['color']};"
        
        elif background_config["type"] == "image":
            # 图片背景
            image_path = background_config["image_path"]
            if os.path.exists(image_path):
                style += f"""
                    background-image: url({image_path});
                    background-position: center;
                    background-repeat: no-repeat;
                    background-size: 100% 100%;  // 拉伸图片以填充窗口
                """
            else:
                # 图片不存在时的后备样式
                style += f"background-color: {self.config['window']['background']['color']};"
                print("图片路径不存在，使用纯色背景。")
        
        widget.setStyleSheet(f"QWidget {{ {style} }}")
        widget.update()  # 确保样式更新

    def set_background_color(self, color):
        """设置纯色背景"""
        self.config["window"]["background"] = {
            "type": "color",
            "color": color
        }
        self.save_config()
        self.apply_background_style(self.centralWidget())

    def set_background_image(self, image_path, size='cover', position='center', repeat='no-repeat'):
        """设置图片背景
        Args:
            image_path (str): 图片路径
            size (str): 图片大小 (cover/contain/100% 100%/等)
            position (str): 图片位置 (center/top/bottom/等)
            repeat (str): 重复方式 (no-repeat/repeat/repeat-x/repeat-y)
        """
        self.config["window"]["background"] = {
            "type": "image",
            "image_path": image_path,
            "size": size,
            "position": position,
            "repeat": repeat
        }
        self.save_config()
        self.apply_background_style(self.centralWidget())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    task_tree = TaskTree()
    # 直接启动 MiniModeWindow
    mini_mode_window = MiniModeWindow(TaskManagerUI(task_tree))
    mini_mode_window.show()
    sys.exit(app.exec_())
