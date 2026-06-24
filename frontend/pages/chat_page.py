"""
问答页 — 聊天界面 + 流式渲染 + 反馈按钮。

布局:
  ┌─ 状态标签 ──────────────────────────────────────┐
  ├─ 聊天记录（QTextBrowser，支持 Markdown）         │
  ├─ 反馈按钮 [👍] [👎] [🤷]                      │
  ├─ 输入框 + [发送] [■停止]                      │
  └──────────────────────────────────────────────┘
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextBrowser,
    QLineEdit,
    QPushButton,
    QLabel,
    QSizePolicy,
)


class ChatPage(QWidget):
    """问答 Tab 页。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """构建 UI。"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # 状态标签
        self.status_label = QLabel("💡 输入问题开始学习")
        self.status_label.setStyleSheet("color: #64748b; font-size: 12px;")
        layout.addWidget(self.status_label)

        # 聊天记录
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        self.browser.setStyleSheet("""
            QTextBrowser {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                line-height: 1.6;
            }
        """)
        layout.addWidget(self.browser, stretch=1)

        # 反馈按钮
        feedback_layout = QHBoxLayout()
        feedback_layout.setSpacing(6)
        self.btn_useful = QPushButton("👍 有用")
        self.btn_useless = QPushButton("👎 没用")
        self.btn_irrelevant = QPushButton("🤷 不相关")
        for btn in (self.btn_useful, self.btn_useless, self.btn_irrelevant):
            btn.setFixedHeight(30)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #f1f5f9;
                    border: 1px solid #e2e8f0;
                    border-radius: 6px;
                    padding: 4px 12px;
                    font-size: 12px;
                    color: #475569;
                }
                QPushButton:hover {
                    background-color: #e2e8f0;
                }
            """)
            feedback_layout.addWidget(btn)
        feedback_layout.addStretch()
        layout.addLayout(feedback_layout)

        # 输入区
        input_layout = QHBoxLayout()
        input_layout.setSpacing(6)

        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("💬 输入问题...")
        self.input_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 14px;
                background-color: #ffffff;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
            }
        """)
        input_layout.addWidget(self.input_edit, stretch=1)

        self.btn_send = QPushButton("📤 发送")
        self.btn_send.setFixedHeight(38)
        self.btn_send.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 20px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
            QPushButton:disabled {
                background-color: #94a3b8;
            }
        """)
        input_layout.addWidget(self.btn_send)

        self.btn_stop = QPushButton("■")
        self.btn_stop.setFixedSize(38, 38)
        self.btn_stop.setToolTip("停止生成")
        self.btn_stop.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
        """)
        input_layout.addWidget(self.btn_stop)

        layout.addLayout(input_layout)

        # 初始欢迎
        self._show_welcome()

    def _show_welcome(self) -> None:
        """显示欢迎信息。"""
        self.browser.setHtml("""
            <div style="text-align: center; padding: 40px 20px; color: #94a3b8;">
                <h2 style="color: #1e293b; margin-bottom: 8px;">🧠 超级导师</h2>
                <p>上传文档后即可开始提问</p>
                <p style="font-size: 13px; margin-top: 20px;">
                    支持 PDF · DOCX · Markdown · TXT
                </p>
            </div>
        """)

    def add_user_message(self, text: str) -> None:
        """添加用户消息。"""
        self.browser.append(
            f'<div style="margin: 8px 0; padding: 8px 12px; '
            f'background-color: #eff6ff; border-radius: 8px; '
            f'border-left: 3px solid #3b82f6;">'
            f'<b style="color: #1e293b;">🧑 您</b><br>{text}</div>'
        )

    def add_assistant_token(self, token: str) -> None:
        """追加助手 token（流式）。"""
        self.browser.insertPlainText(token)
        # 滚动到底部
        scrollbar = self.browser.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def add_assistant_done(self, full_text: str) -> None:
        """助手回答完成，添加来源标注。"""
        self.browser.append(
            f'<div style="margin: 4px 0; padding: 4px 0; '
            f'font-size: 11px; color: #94a3b8;">'
            f'[来源: 文档自动标注]</div>'
        )
