"""
课程选择器 — 标题栏下拉框 + 新建/改名/删除。

从 courses.json 加载课程列表，提供下拉选择、新建、重命名、删除操作。
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QComboBox,
    QPushButton,
    QInputDialog,
    QMessageBox,
)


# ── 默认课程配置路径 ──────────────────────────────────────

COURSES_JSON = Path("knowledge_base/index/courses.json")


def _default_courses() -> list[dict]:
    """返回默认课程列表。"""
    return [{"id": str(uuid.uuid4()), "name": "课程 1", "organize_by": "auto", "created_at": datetime.now().isoformat()}]


def load_courses() -> list[dict]:
    """从 courses.json 加载课程列表，文件不存在则创建默认。"""
    if not COURSES_JSON.exists():
        COURSES_JSON.parent.mkdir(parents=True, exist_ok=True)
        courses = _default_courses()
        save_courses(courses)
        return courses
    try:
        with open(COURSES_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        courses = _default_courses()
        save_courses(courses)
        return courses


def save_courses(courses: list[dict]) -> None:
    """保存课程列表到 courses.json。"""
    COURSES_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(COURSES_JSON, "w", encoding="utf-8") as f:
        json.dump(courses, f, ensure_ascii=False, indent=2)


# ── 课程选择器组件 ────────────────────────────────────────


class CourseSelector(QWidget):
    """标题栏的课程选择器组件。

    包含下拉框 + 新建按钮。
    切换课程时发射 course_changed(str) 信号。
    """

    course_changed = Signal(str)  # 课程名

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._courses: list[dict] = []
        self._setup_ui()
        self._load()

    def _setup_ui(self) -> None:
        """构建 UI：下拉框 + 新建按钮。"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 2, 10, 2)
        layout.setSpacing(6)

        self.combo = QComboBox()
        self.combo.setMinimumWidth(180)
        self.combo.currentIndexChanged.connect(self._on_selected)
        layout.addWidget(self.combo)

        self.btn_new = QPushButton("+ 新建")
        self.btn_new.setFixedSize(70, 28)
        self.btn_new.clicked.connect(self._add_course)
        layout.addWidget(self.btn_new)

        self.btn_rename = QPushButton("✏️")
        self.btn_rename.setFixedSize(32, 28)
        self.btn_rename.setToolTip("重命名当前课程")
        self.btn_rename.clicked.connect(self._rename_course)
        layout.addWidget(self.btn_rename)

        self.btn_delete = QPushButton("🗑️")
        self.btn_delete.setFixedSize(32, 28)
        self.btn_delete.setToolTip("删除当前课程")
        self.btn_delete.clicked.connect(self._delete_course)
        layout.addWidget(self.btn_delete)

    def _load(self) -> None:
        """加载课程列表到下拉框。"""
        self._courses = load_courses()
        self.combo.blockSignals(True)
        self.combo.clear()
        for c in self._courses:
            self.combo.addItem(c["name"], c["id"])
        self.combo.blockSignals(False)
        if self._courses:
            self.combo.setCurrentIndex(0)

    # ── 操作 ─────────────────────────────────────────────

    def _on_selected(self, index: int) -> None:
        """课程切换。"""
        if 0 <= index < len(self._courses):
            self.course_changed.emit(self._courses[index]["name"])

    def _add_course(self) -> None:
        """新建课程，默认名 课程 N。"""
        n = len(self._courses) + 1
        name = f"课程 {n}"
        new_course = {
            "id": str(uuid.uuid4()),
            "name": name,
            "organize_by": "auto",
            "created_at": datetime.now().isoformat(),
        }
        self._courses.append(new_course)
        save_courses(self._courses)
        self.combo.addItem(name, new_course["id"])
        self.combo.setCurrentIndex(self.combo.count() - 1)

    def _rename_course(self) -> None:
        """重命名当前课程。"""
        idx = self.combo.currentIndex()
        if idx < 0:
            return
        old_name = self._courses[idx]["name"]
        new_name, ok = QInputDialog.getText(self, "重命名课程", "新名称：", text=old_name)
        if ok and new_name.strip():
            self._courses[idx]["name"] = new_name.strip()
            save_courses(self._courses)
            self.combo.setItemText(idx, new_name.strip())
            self.course_changed.emit(new_name.strip())

    def _delete_course(self) -> None:
        """删除当前课程。"""
        idx = self.combo.currentIndex()
        if idx < 0:
            return
        name = self._courses[idx]["name"]
        confirm = QMessageBox.question(
            self,
            "删除课程",
            f"确定删除「{name}」吗？\n该课程的所有文档和进度数据将被清除。",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            self._courses.pop(idx)
            save_courses(self._courses)
            self.combo.removeItem(idx)
            if self._courses:
                self.combo.setCurrentIndex(0)
                self.course_changed.emit(self._courses[0]["name"])

    @property
    def current_course(self) -> str:
        """返回当前选中的课程名。"""
        idx = self.combo.currentIndex()
        if 0 <= idx < len(self._courses):
            return self._courses[idx]["name"]
        return ""
