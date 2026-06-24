"""
规划+进度页 — 复习计划 + 打勾标记 + 进度条。

布局:
  ┌─ 参数设置（天数 + 小时 + [生成]）─────────────────┐
  ├─ 每日任务卡片（可勾选 + 进度条）                   │
  ├─ 整体进度条 + 已学章节                            │
  ├─ [重新生成（跳过已学）]  [导出计划]               │
  └──────────────────────────────────────────────┘
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QScrollArea,
    QPushButton,
    QLabel,
    QCheckBox,
    QProgressBar,
    QSpinBox,
    QFrame,
)


class PlanPage(QWidget):
    """规划+进度 Tab 页。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """构建 UI。"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        # ── 参数设置 ──────────────────────────────
        params_layout = QHBoxLayout()
        params_layout.setSpacing(8)

        params_layout.addWidget(QLabel("目标:"))
        self.days_spin = QSpinBox()
        self.days_spin.setRange(1, 365)
        self.days_spin.setValue(30)
        self.days_spin.setSuffix(" 天")
        params_layout.addWidget(self.days_spin)

        params_layout.addWidget(QLabel("每天:"))
        self.hours_spin = QSpinBox()
        self.hours_spin.setRange(1, 16)
        self.hours_spin.setValue(2)
        self.hours_spin.setSuffix(" 小时")
        params_layout.addWidget(self.hours_spin)

        self.btn_generate = QPushButton("📅 生成计划")
        self.btn_generate.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #2563eb; }
        """)
        params_layout.addWidget(self.btn_generate)
        params_layout.addStretch()

        layout.addLayout(params_layout)

        # ── 计划内容 ──────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")

        self.plan_container = QWidget()
        self.plan_layout = QVBoxLayout(self.plan_container)
        self.plan_layout.setSpacing(8)
        self.plan_layout.setContentsMargins(0, 0, 0, 0)

        scroll.setWidget(self.plan_container)
        layout.addWidget(scroll, stretch=1)

        # ── 整体进度 ──────────────────────────────
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("整体进度: %p%")
        self.progress_bar.setFixedHeight(24)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                text-align: center;
                font-size: 12px;
                color: #1e293b;
                background-color: #f1f5f9;
            }
            QProgressBar::chunk {
                background-color: #3b82f6;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.progress_bar)

        self.label_completed = QLabel("已掌握章节: 无")
        self.label_completed.setStyleSheet("color: #64748b; font-size: 12px;")
        layout.addWidget(self.label_completed)

        # ── 操作按钮 ──────────────────────────────
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(8)

        self.btn_regenerate = QPushButton("🔄 重新生成（跳过已学）")
        self.btn_regenerate.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
                color: #475569;
            }
            QPushButton:hover { background-color: #e2e8f0; }
        """)
        actions_layout.addWidget(self.btn_regenerate)

        self.btn_export = QPushButton("📤 导出计划")
        self.btn_export.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
                color: #475569;
            }
            QPushButton:hover { background-color: #e2e8f0; }
        """)
        actions_layout.addWidget(self.btn_export)
        actions_layout.addStretch()

        layout.addLayout(actions_layout)

        # 初始空状态
        self._show_empty_state()

    def _show_empty_state(self) -> None:
        """空状态提示。"""
        self._clear_plan()
        label = QLabel("📋 设置天数和学时，点击生成计划")
        label.setStyleSheet("color: #94a3b8; font-size: 14px; padding: 40px;")
        label.setAlignment(Qt.AlignCenter)
        self.plan_layout.addWidget(label)

    def _clear_plan(self) -> None:
        """清空计划内容。"""
        while self.plan_layout.count():
            item = self.plan_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def add_day_card(self, day: int, title: str, tasks: list[str]) -> QWidget:
        """添加一天的任务卡片。

        Args:
            day: 第几天。
            title: 标题（如 "第一章 绪论"）。
            tasks: 任务列表。

        Returns:
            卡片 widget（可后续更新进度）。
        """
        # 清除空状态
        if self.plan_layout.count() == 1:
            first = self.plan_layout.itemAt(0)
            if first and first.widget():
                text = first.widget().findChild(QLabel)
                if text and "设置天数" in text.text():
                    self._clear_plan()

        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 12px;
            }
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(4)

        # 标题
        header = QLabel(f"📅 第 {day} 天 — {title}")
        header.setStyleSheet("font-weight: 600; font-size: 13px; color: #1e293b;")
        card_layout.addWidget(header)

        # 任务列表
        checked = 0
        for task in tasks:
            cb = QCheckBox(task)
            cb.setStyleSheet("font-size: 12px; color: #475569; padding: 2px 0;")
            cb.toggled.connect(self._update_progress)
            card_layout.addWidget(cb)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #f1f5f9;")
        card_layout.addWidget(line)

        # 进度条
        progress = QProgressBar()
        progress.setRange(0, len(tasks))
        progress.setValue(0)
        progress.setTextVisible(True)
        progress.setFormat(f"已完成 0/{len(tasks)}")
        progress.setFixedHeight(16)
        progress.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 4px;
                text-align: center;
                font-size: 11px;
                color: #64748b;
                background-color: #f1f5f9;
            }
            QProgressBar::chunk {
                background-color: #22c55e;
                border-radius: 4px;
            }
        """)
        card_layout.addWidget(progress)

        self.plan_layout.addWidget(card)
        return card

    def _update_progress(self) -> None:
        """更新所有进度条（复选框 toggled 触发）。"""
        # 遍历所有卡片，重新计算进度
        total_tasks = 0
        total_done = 0
        days = 0

        for i in range(self.plan_layout.count()):
            item = self.plan_layout.itemAt(i)
            if not item or not item.widget():
                continue
            card = item.widget()
            # 只处理 QFrame 卡片
            if not isinstance(card, QFrame):
                continue

            checkboxes = card.findChildren(QCheckBox)
            progress_bar = card.findChildren(QProgressBar)
            if not progress_bar:
                continue

            done = sum(1 for cb in checkboxes if cb.isChecked())
            total = len(checkboxes)
            days += 1

            progress_bar[0].setValue(done)
            progress_bar[0].setFormat(f"已完成 {done}/{total}")

            total_done += done
            total_tasks += total

        # 更新整体进度
        if total_tasks > 0:
            pct = int(total_done / total_tasks * 100)
            self.progress_bar.setValue(pct)
            self.progress_bar.setFormat(f"整体进度: {pct}% ({total_done}/{total_tasks})")
