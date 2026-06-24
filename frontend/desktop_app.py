"""
超级导师主窗口 — 现代化无边框设计。

特点:
  - 无边框窗口 + 自定义标题栏（可拖拽）
  - 精致暗色主题（深灰+蓝紫 accent）
  - 毛玻璃效果标题栏
  - 圆角三区布局
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import QFont, QIcon, QAction, QPixmap, QPainter, QColor, QLinearGradient, QBrush, QPen
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QSplitter,
    QTabWidget,
    QStatusBar,
    QPushButton,
    QLabel,
    QFrame,
    QGraphicsDropShadowEffect,
    QSizePolicy,
)

from frontend.components.course_selector import CourseSelector
from frontend.components.document_tree import DocumentTree
from frontend.components.settings_dialog import SettingsDialog
from frontend.pages.chat_page import ChatPage
from frontend.pages.plan_page import PlanPage


# ── 调色板 ──────────────────────────────────────────────────
# Impeccable: Restrained 策略，避开 AI 默认奶油色
# 深色主题，蓝紫 accent

COLORS = {
    "bg_primary": "#0f1117",       # 主背景 - 极深灰
    "bg_secondary": "#181b24",     # 二级背景 - 深灰
    "bg_tertiary": "#1e2231",      # 三级背景 - 灰蓝
    "bg_card": "#1c2030",          # 卡片背景
    "bg_surface": "#242838",       # 表面色
    "accent": "#6c63ff",           # 主 accent - 紫蓝
    "accent_hover": "#7c73ff",     # accent 悬停
    "accent_subtle": "#6c63ff20",  # accent 10% 透明度
    "text_primary": "#e8eaf0",     # 主文字
    "text_secondary": "#8b8fa3",   # 次要文字
    "text_muted": "#5a5e72",       # 禁用文字
    "border": "#2a2e3d",           # 边框
    "border_light": "#35394a",     # 浅边框
    "success": "#34d399",          # 成功
    "warning": "#fbbf24",          # 警告
    "error": "#f87171",            # 错误
    "title_bg": "rgba(15, 17, 23, 0.85)",  # 标题栏背景
}


# ── 自定义标题栏 ─────────────────────────────────────────────


class TitleBar(QWidget):
    """无边框窗口的自定义标题栏（可拖拽）。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._parent = parent
        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        self.setFixedHeight(52)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 0, 0)
        layout.setSpacing(6)

        # 应用图标 + 标题
        self.icon_label = QLabel("🧠")
        self.icon_label.setFixedSize(28, 28)
        layout.addWidget(self.icon_label)

        self.title_label = QLabel("超级导师")
        self.title_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 15px; font-weight: 700; letter-spacing: 0.5px;")
        layout.addWidget(self.title_label)

        self.subtitle_label = QLabel("Super-Tutor")
        self.subtitle_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; font-weight: 400; padding-top: 4px;")
        layout.addWidget(self.subtitle_label)

        # 课程选择器
        self.course_selector = CourseSelector()
        layout.addWidget(self.course_selector)

        layout.addStretch()

        # 窗口控制按钮
        for icon, tooltip, callback in [
            ("—", "最小化", self._parent.showMinimized),
            ("□", "最大化", self._toggle_maximize),
            ("✕", "关闭", self._parent.close),
        ]:
            btn = QPushButton(icon)
            btn.setFixedSize(46, 32)
            btn.setToolTip(tooltip)
            btn.clicked.connect(callback)
            btn.setProperty("role", tooltip)
            layout.addWidget(btn)

        self._maximized = False

    def _apply_style(self) -> None:
        self.setStyleSheet(f"""
            TitleBar {{
                background-color: {COLORS['title_bg']};
                border-bottom: 1px solid {COLORS['border']};
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }}
            TitleBar QPushButton {{
                background: transparent;
                color: {COLORS['text_secondary']};
                border: none;
                font-size: 14px;
                font-weight: 400;
                border-radius: 6px;
            }}
            TitleBar QPushButton:hover {{
                background-color: {COLORS['bg_tertiary']};
                color: {COLORS['text_primary']};
            }}
            TitleBar QPushButton[role="关闭"]:hover {{
                background-color: #ef4444;
                color: white;
            }}
        """)

    def _toggle_maximize(self) -> None:
        if self._maximized:
            self._parent.showNormal()
        else:
            self._parent.showMaximized()
        self._maximized = not self._maximized

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()
            self._is_dragging = True
            event.accept()

    def mouseMoveEvent(self, event) -> None:
        if hasattr(self, '_is_dragging') and self._is_dragging and self._parent:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self._parent.move(self._parent.pos() + delta)
            self._drag_pos = event.globalPosition().toPoint()
            event.accept()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._is_dragging = False
            event.accept()


# ── 毛玻璃卡片容器 ───────────────────────────────────────────


class GlassCard(QFrame):
    """毛玻璃效果卡片容器。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet(f"""
            GlassCard {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)


# ── 主窗口 ───────────────────────────────────────────────────


class SuperTutorWindow(QMainWindow):
    """超级导师主窗口（无边框）。"""

    def __init__(self) -> None:
        super().__init__()
        self._setup_window()
        self._build_layout()
        self._apply_theme()

    def _setup_window(self) -> None:
        """窗口基础属性。"""
        self.setWindowTitle("超级导师 Super-Tutor")
        self.setMinimumSize(1100, 700)
        self.resize(1300, 850)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 居中
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2,
        )

    def _build_layout(self) -> None:
        """构建完整布局。"""
        # 外层容器（圆角 + 阴影）
        outer = QWidget()
        outer.setObjectName("outerContainer")
        outer.setStyleSheet(f"""
            #outerContainer {{
                background-color: {COLORS['bg_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 14px;
                margin: 0px;
            }}
        """)

        # 阴影
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(48)
        shadow.setColor(QColor(0, 0, 0, 120))
        shadow.setOffset(0, 8)
        outer.setGraphicsEffect(shadow)

        main_layout = QVBoxLayout(outer)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 标题栏
        self.title_bar = TitleBar(self)
        main_layout.addWidget(self.title_bar)

        # 连接课程切换
        selector = self.title_bar.course_selector
        selector.course_changed.connect(self._on_course_changed)

        # 中央三区
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {COLORS['border']};
                width: 1px;
            }}
        """)

        # 左侧：知识库
        self.doc_tree = DocumentTree()
        splitter.addWidget(self.doc_tree)

        # 右侧：Tab 页
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.chat_page = ChatPage()
        self.plan_page = PlanPage()
        self.tabs.addTab(self.chat_page, "💬  问答")
        self.tabs.addTab(self.plan_page, "📅  规划 + 进度")
        splitter.addWidget(self.tabs)

        splitter.setSizes([280, 820])
        splitter.setChildrenCollapsible(False)

        main_layout.addWidget(splitter, stretch=1)

        # 状态栏
        self._setup_status_bar()
        main_layout.addWidget(self._status_widget)

        self.setCentralWidget(outer)

    def _setup_status_bar(self) -> None:
        """现代化状态栏。"""
        self._status_widget = QWidget()
        self._status_widget.setFixedHeight(36)
        self._status_widget.setStyleSheet(f"""
            background-color: {COLORS['bg_secondary']};
            border-top: 1px solid {COLORS['border']};
            border-bottom-left-radius: 12px;
            border-bottom-right-radius: 12px;
        """)

        layout = QHBoxLayout(self._status_widget)
        layout.setContentsMargins(16, 0, 16, 0)

        self.status_icon = QLabel("●")
        self.status_icon.setStyleSheet(f"color: {COLORS['success']}; font-size: 8px;")
        layout.addWidget(self.status_icon)

        self.status_label = QLabel("就绪 — 请上传文档开始学习")
        self.status_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
        layout.addWidget(self.status_label)

        layout.addStretch()

    def _on_course_changed(self, course_name: str) -> None:
        """课程切换时的全局更新。"""
        self.status_label.setText(f"当前课程: {course_name}")
        # 后续从这里触发知识库刷新/问答切换/计划加载

    # ── 主题 ────────────────────────────────────────────────

    def _apply_theme(self) -> None:
        """全局现代化主题。"""
        self.setStyleSheet(f"""
            /* 全局 */
            QWidget {{
                font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", "Noto Sans CJK";
                color: {COLORS['text_primary']};
            }}
            QMainWindow {{
                background: transparent;
            }}
            /* Tab 栏 */
            QTabWidget::pane {{
                background-color: {COLORS['bg_primary']};
                border: none;
                border-top: 1px solid {COLORS['border']};
                border-radius: 0;
            }}
            QTabBar::tab {{
                background-color: {COLORS['bg_secondary']};
                color: {COLORS['text_muted']};
                padding: 10px 24px;
                margin-right: 0px;
                border: none;
                border-bottom: 2px solid transparent;
                font-size: 13px;
                font-weight: 500;
                min-width: 100px;
            }}
            QTabBar::tab:selected {{
                background-color: {COLORS['bg_primary']};
                color: {COLORS['accent']};
                border-bottom: 2px solid {COLORS['accent']};
            }}
            QTabBar::tab:hover {{
                color: {COLORS['text_primary']};
            }}
            /* 滚动条 */
            QScrollBar:vertical {{
                width: 6px;
                background: transparent;
                margin: 4px 0;
            }}
            QScrollBar::handle:vertical {{
                background: {COLORS['border_light']};
                border-radius: 3px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {COLORS['text_muted']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
            QScrollBar:horizontal {{
                height: 6px;
                background: transparent;
            }}
            QScrollBar::handle:horizontal {{
                background: {COLORS['border_light']};
                border-radius: 3px;
            }}
            QSplitter {{
                background-color: {COLORS['bg_primary']};
            }}
        """)


# ── 启动 ────────────────────────────────────────────────────


def main() -> None:
    """应用入口。"""
    app = QApplication(sys.argv)

    # 字体
    font = QFont()
    font.setFamilies(["Segoe UI", "PingFang SC", "Microsoft YaHei", "Noto Sans CJK"])
    font.setPointSize(10)
    app.setFont(font)

    # 全局暗色高亮
    palette = app.palette()
    palette.setColor(palette.Highlight, QColor(COLORS["accent"]))
    palette.setColor(palette.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)

    window = SuperTutorWindow()
    window.show()

    sys.exit(app.exec())
