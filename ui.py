import sys
import keyboard  # Import the keyboard library for global hotkeys
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QVBoxLayout, QPushButton, QWidget, QMessageBox, QLabel, QMenu, QLineEdit
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt
from task_tree import TaskTree

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
        
        layout.addWidget(add_task_btn)
        layout.addWidget(complete_task_btn)
        layout.addWidget(mini_mode_btn)
        
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
            QMessageBox.warning(self, "警告", "根节点不可完成。")
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

class MiniModeWindow(QMainWindow):
    def __init__(self, task_manager_ui):
        super().__init__()
        self.task_manager_ui = task_manager_ui
        self.initUI()
        self.offset = None  # 用于存储鼠标点击位置的偏移量

    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)  # 允许背景颜色设置
        self.setGeometry(100, 100, 200, 50)

        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.update_task_name()

        self.input_field = QLineEdit(self)
        self.input_field.setAlignment(Qt.AlignCenter)
        self.input_field.hide()  # 初始隐藏输入框
        self.input_field.returnPressed.connect(self.rename_task)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.input_field)

        central_widget = QWidget(self)
        central_widget.setLayout(layout)
        central_widget.setStyleSheet("background-color: white;")  # 设置背景颜色为白色
        self.setCentralWidget(central_widget)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def update_task_name(self):
        """更新悬浮条上的任务名称"""
        self.label.setText(self.task_manager_ui.task_tree.current_task.name)

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
            self.offset = event.pos()  # 记录鼠标点击位置

    def mouseMoveEvent(self, event):
        if self.offset is not None:
            self.move(self.pos() + event.pos() - self.offset)  # 移动窗口

    def mouseReleaseEvent(self, event):
        self.offset = None  # 重置偏移量

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.task_manager_ui.show()
            self.close()

    def rename_task(self):
        """重命名任务并更新显示"""
        new_name = self.input_field.text().strip()
        if new_name:
            self.task_manager_ui.task_tree.rename_task(new_name)
            self.task_manager_ui.update_ui_signal.emit()  # 更新 UI
            self.task_manager_ui.task_changed_signal.emit()  # 通知任务切换
        self.input_field.hide()
        self.label.show()
        self.update_task_name()

    def enter_rename_mode(self):
        """进入重命名模式"""
        self.label.hide()
        self.input_field.setText(self.task_manager_ui.task_tree.current_task.name)
        self.input_field.show()
        self.input_field.setFocus()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    task_tree = TaskTree()
    ui = TaskManagerUI(task_tree)
    ui.show()
    sys.exit(app.exec_())
