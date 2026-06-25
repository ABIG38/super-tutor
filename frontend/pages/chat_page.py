"""
问答页 — 精简版：直接调 agent 流式接口。
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTextBrowser, QLineEdit, QPushButton, QLabel,
)


class AskThread(QThread):
    token = Signal(str)
    done = Signal()
    error = Signal(str)

    def __init__(self, agent, query, course):
        super().__init__()
        self._agent = agent
        self._query = query
        self._course = course

    def run(self):
        try:
            for t in self._agent.ask(self._query, course=self._course):
                self.token.emit(t)
            self.done.emit()
        except Exception as e:
            self.error.emit(str(e))


class ChatPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._agent = None
        self._course = ""
        self._thread = None
        self._setup_ui()

    def set_agent(self, agent):
        self._agent = agent

    def set_course(self, course: str):
        self._course = course

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 32, 40, 32)
        layout.setSpacing(16)

        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        self.browser.setStyleSheet("QTextBrowser { background-color: transparent; border: none; font-size: 14px; line-height: 1.8; color: #fcfcfc; }")
        layout.addWidget(self.browser, stretch=1)
        self._welcome()

        input_layout = QHBoxLayout()
        input_layout.setSpacing(12)

        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("输入您的问题...")
        self.input_edit.setStyleSheet("QLineEdit { border: 1px solid #1f1f22; border-radius: 8px; padding: 12px 20px; font-size: 13px; background-color: #0f0f11; color: #fcfcfc; } QLineEdit:focus { border-color: #ccff00; }")
        self.input_edit.returnPressed.connect(self._send)
        input_layout.addWidget(self.input_edit, stretch=1)

        self.btn_plan = QPushButton("📅 计划")
        self.btn_plan.setFixedSize(100, 42)
        self.btn_plan.setStyleSheet("QPushButton { background-color: transparent; color: #ccff00; border: 1px solid #ccff00; border-radius: 8px; font-size: 11px; font-weight: 800; } QPushButton:hover { background-color: #ccff00; color: #050505; }")
        self.btn_plan.clicked.connect(self._generate_plan)
        input_layout.addWidget(self.btn_plan)

        self.btn_send = QPushButton("发送")
        self.btn_send.setFixedSize(100, 42)
        self.btn_send.setStyleSheet("QPushButton { background-color: #ccff00; color: #050505; border: none; border-radius: 8px; font-size: 12px; font-weight: 800; } QPushButton:hover { background-color: #d9ff33; }")
        self.btn_send.clicked.connect(self._send)
        input_layout.addWidget(self.btn_send)

        self.btn_stop = QPushButton("停止")
        self.btn_stop.setFixedSize(80, 42)
        self.btn_stop.setStyleSheet("QPushButton { background-color: transparent; color: #ff3333; border: 1px solid #ff3333; border-radius: 8px; font-size: 12px; font-weight: 800; }")
        self.btn_stop.clicked.connect(self._stop)
        input_layout.addWidget(self.btn_stop)

        layout.addLayout(input_layout)

    def _welcome(self):
        self.browser.setHtml('<div style="text-align:left;padding:40px 0;color:#55555a;"><h1 style="color:#fcfcfc;font-weight:800;font-size:32px;letter-spacing:2px;">超级导师</h1><p style="font-size:13px;">上传文档后即可开始提问。</p><div style="display:inline-block;border:1px solid #1f1f22;border-radius:4px;padding:6px 12px;font-size:10px;color:#a0a0a5;">支持 PDF, DOCX, MD, TXT</div></div>')

    def _send(self):
        query = self.input_edit.text().strip()
        if not query:
            return
        if self._agent is None:
            from backend.agent.orchestrator import SuperTutorAgent
            self._agent = SuperTutorAgent()

        self.input_edit.setEnabled(False)
        self.btn_send.setEnabled(False)

        self._add_user_msg(query)
        self._start_assistant()

        self._thread = AskThread(self._agent, query, self._course)
        self._thread.token.connect(self._on_token)
        self._thread.done.connect(self._on_done)
        self._thread.error.connect(self._on_error)
        self._thread.finished.connect(self._finish)
        self._thread.start()
        self.input_edit.clear()

    def _stop(self):
        if self._agent:
            self._agent.cancel_stream()
        self._finish()

    def _on_token(self, t: str):
        cursor = self.browser.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(t)
        self.browser.setTextCursor(cursor)
        sb = self.browser.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _on_done(self):
        pass

    def _on_error(self, msg: str):
        self.browser.append(f'<div style="color:#ff3333;margin:8px 0;">⚠ {msg}</div>')

    def _finish(self):
        self.input_edit.setEnabled(True)
        self.btn_send.setEnabled(True)

    def _add_user_msg(self, text: str):
        self.browser.append(f'<div style="margin:16px 0;padding:16px 20px;background-color:#0f0f11;border-radius:8px;border:1px solid #1f1f22;"><div style="color:#55555a;font-size:10px;font-weight:700;margin-bottom:8px;">用 户</div><div style="color:#fcfcfc;">{text}</div></div>')

    def _start_assistant(self):
        self.browser.append('<div style="margin:8px 0;color:#ccff00;font-size:10px;font-weight:700;">助 手</div>')

    def _generate_plan(self):
        """简单的计划生成：弹日期输入 → 调 LLM → 显示结果。"""
        if self._agent is None:
            return
        from PySide6.QtWidgets import QInputDialog, QDialog, QVBoxLayout, QTextBrowser, QPushButton
        days, ok = QInputDialog.getInt(self, "学习计划", "总天数：", 30, 1, 365)
        if not ok:
            return
        hours, ok = QInputDialog.getInt(self, "学习计划", "每天学习（小时）：", 2, 1, 16)
        if not ok:
            return

        self.btn_plan.setEnabled(False)
        self.btn_plan.setText("生成中...")
        self._add_user_msg(f"📅 请为我制定 {days} 天、每天 {hours} 小时的学习计划")
        self._start_assistant()

        class PlanThread(QThread):
            done = Signal(str)
            def __init__(self, agent, days, hours, course):
                super().__init__()
                self._agent = agent
                self._days = days
                self._hours = hours
                self._course = course
            def run(self):
                try:
                    r = self._agent.generate_plan(self._days, self._hours, self._course)
                    self.done.emit(r)
                except Exception as e:
                    self.done.emit(f"生成失败：{e}")

        self._plan_thread = PlanThread(self._agent, days, hours, self._course)
        self._plan_thread.done.connect(self._on_plan_done)
        self._plan_thread.start()

    def _on_plan_done(self, text: str):
        self.btn_plan.setEnabled(True)
        self.btn_plan.setText("📅 计划")
        import html
        self.browser.append(f'<div style="margin:8px 0;padding:16px;background-color:#0a0a0c;border:1px solid #1f1f22;border-radius:8px;font-size:13px;line-height:1.7;white-space:pre-wrap;">{html.escape(text)}</div>')
        sb = self.browser.verticalScrollBar()
        sb.setValue(sb.maximum())
