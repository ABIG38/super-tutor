"""
超级导师主窗口 — PySide6 三区布局。

布局:
  ┌─ 标题栏（课程选择器 + 新建 + 设置）──────────────────────┐
  ├─ 知识库列表  ├─ Tab: 问答  |  规划+进度                  │
  ├─ 状态栏 ──────────────────────────────────────────────-┤
  └────────────────────────────────────────────────────────┘

设计原则（Impeccable）:
  - Restrained 色彩：深蓝侧栏 + 白底内容区，单 accent 色
  - 单字体族：系统 UI 字体，清晰层级
  - 无卡片嵌套、无侧边条纹装饰
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon, QAction
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QSplitter,
    QTabWidget,
    QStatusBar,
    QMessageBox,
    QMenu,
    QMenuBar,
)

from frontend.components.course_selector import CourseSelector
from frontend.components.document_tree import DocumentTree
from frontend.components.settings_dialog import SettingsDialog
from frontend.pages.chat_page import ChatPage
from frontend.pages.plan_page import PlanPage


# ── 调色板（Impeccable: Restrained 策略，OKLCH 推导）───────
# 深蓝侧栏 #1a2332 → ink
# 白底内容 #f8f9fa → bg
# 主题色 #3b82f6 → accent (蓝)
# 文字主色 #1e293b → 正文
# 文字辅色 #64748b → 次要

class SuperTutorWindow(QMainWindow):
    """超级导师主窗口。"""

    def __init__(self) -> None:
        super().__init__()
        self._init_window()
        self._init_title_bar()
        self._init_central_area()
        self._init_status_bar()
        self._apply_theme()

    # ── 窗口基础 ─────────────────────────────────────────

    def _init_window(self) -> None:
        """设置窗口基本属性。"""
        self.setWindowTitle("超级导师 Super-Tutor")
        self.setMinimumSize(QSize(1100, 700))
        self.resize(1300, 850)
        # 居中
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2,
        )

    # ── 标题栏 ───────────────────────────────────────────

    def _init_title_bar(self) -> None:
        """标题栏：课程选择器 + 新建 + 设置（嵌入菜单栏模拟）。"""
        menu_bar = self.menuBar()

        # 课程选择器（作为自定义 widget 嵌入 menu bar）
        self.course_selector = CourseSelector()
        menu_bar.setCornerWidget(self.course_selector, Qt.TopLeftCorner)

        # 设置按钮
        settings_action = QAction("⚙️ 设置", self)
        settings_action.triggered.connect(self._open_settings)
        menu_bar.addAction(settings_action)

    # ── 中央三区 ────────────────────────────────────────

    def _init_central_area(self) -> None:
        """三区布局：左侧知识库 | 右侧 Tab 页。"""
        splitter = QSplitter(Qt.Horizontal)

        # 左侧：知识库列表
        self.doc_tree = DocumentTree()
        splitter.addWidget(self.doc_tree)

        # 右侧：Tab 页
        self.tabs = QTabWidget()
        self.chat_page = ChatPage()
        self.plan_page = PlanPage()
        self.tabs.addTab(self.chat_page, "💬 问答")
        self.tabs.addTab(self.plan_page, "📅 规划+进度")
        splitter.addWidget(self.tabs)

        # 比例 1:3
        splitter.setSizes([280, 820])
        splitter.setChildrenCollapsible(False)

        self.setCentralWidget(splitter)

    # ── 状态栏 ──────────────────────────────────────────

    def _init_status_bar(self) -> None:
        """底部状态栏。"""
        self.status = QStatusBar()
        self.status.showMessage("✅ 就绪 — 请上传文档开始学习")
        self.setStatusBar(self.status)

    # ── 主题 ────────────────────────────────────────────

    def _apply_theme(self) -> None:
        """全局样式表（Impeccable 设计原则）。"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            QMenuBar {
                background-color: #1a2332;
                color: #e2e8f0;
                padding: 4px 0;
                font-size: 13px;
            }
            QMenuBar::item:selected {
                background-color: #2d3a4f;
                border-radius: 4px;
            }
            QTabWidget::pane {
                border: none;
                background-color: #f8f9fa;
            }
            QTabBar::tab {
                background-color: #e2e8f0;
                color: #475569;
                padding: 8px 20px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-size: 13px;
            }
            QTabBar::tab:selected {
                background-color: #ffffff;
                color: #1e293b;
                font-weight: 600;
            }
            QSplitter::handle {
                background-color: #e2e8f0;
                width: 2px;
            }
            QStatusBar {
                background-color: #1a2332;
                color: #94a3b8;
                font-size: 12px;
                padding: 2px 10px;
            }
            QScrollBar:vertical {
                width: 8px;
                background: transparent;
            }
            QScrollBar::handle:vertical {
                background: #cbd5e1;
                border-radius: 4px;
                min-height: 30px;
            }
        """)

    # ── 对话框 ──────────────────────────────────────────

    def _open_settings(self) -> None:
        """打开设置对话框。"""
        dialog = SettingsDialog(self)
        dialog.exec()


# ── 启动 ──────────────────────────────────────────────────


def main() -> None:
    """应用入口。"""
    app = QApplication(sys.argv)

    # 字体（Impeccable: 单字体族，系统 UI 字体）
    font = QFont()
    font.setFamilies(["Segoe UI", "PingFang SC", "Microsoft YaHei", "Noto Sans CJK"])
    font.setPointSize(10)
    app.setFont(font)

    window = SuperTutorWindow()
    window.show()

    sys.exit(app.exec())
