"""
知识库文档树 — 精简版，直接调 agent。
"""
from __future__ import annotations

from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTreeWidget, QTreeWidgetItem, QPushButton,
    QFileDialog, QMessageBox, QMenu, QInputDialog,
)


class DocumentTree(QWidget):
    def __init__(self, agent, parent=None):
        super().__init__(parent)
        self._agent = agent
        self._course = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        header = QWidget()
        header.setFixedHeight(48)
        header.setStyleSheet("background-color: #050505; border-bottom: 1px solid #1f1f22;")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(20, 0, 20, 0)
        title = QLabel("知识库")
        title.setStyleSheet("color: #a0a0a5; font-size: 11px; font-weight: 700; letter-spacing: 2px;")
        hl.addWidget(title)
        self.btn_upload = QPushButton("+ 添加")
        self.btn_upload.setFixedSize(56, 24)
        self.btn_upload.setStyleSheet("QPushButton { background-color: transparent; color: #ccff00; border: 1px solid #ccff00; border-radius: 4px; font-size: 10px; font-weight: 700; } QPushButton:hover { background-color: #ccff00; color: #050505; }")
        self.btn_upload.clicked.connect(self._upload)
        hl.addWidget(self.btn_upload)
        layout.addWidget(header)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(12)
        self.tree.setAnimated(True)
        self.tree.setStyleSheet("QTreeWidget { background-color: #0f0f11; color: #a0a0a5; border: none; font-size: 12px; padding: 12px 8px; } QTreeWidget::item { padding: 8px 12px; border-radius: 4px; } QTreeWidget::item:hover { background-color: #1a1a1d; color: #fcfcfc; } QTreeWidget::item:selected { background-color: #ccff0015; color: #ccff00; border-left: 2px solid #ccff00; }")
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._context_menu)
        layout.addWidget(self.tree)
        self._refresh()

    def _upload(self):
        files, _ = QFileDialog.getOpenFileNames(self, "选择文档", "", "文档 (*.pdf *.docx *.md *.txt);;所有文件 (*)")
        for f in files:
            path = Path(f)
            result = self._agent.ingest_document(str(path), course=self._course)
            if result.get("ok"):
                self._refresh()
            elif result.get("reason") == "duplicate":
                r = QMessageBox.question(self, "重复", f"「{path.name}」已存在，覆盖？", QMessageBox.Yes | QMessageBox.No)
                if r == QMessageBox.Yes:
                    self._agent.delete_document(path.name)
                    self._agent.ingest_document(str(path), course=self._course)
                    self._refresh()
            else:
                QMessageBox.warning(self, "错误", f"「{path.name}」: {result.get('reason', '?')}")

    def _refresh(self):
        self.tree.clear()
        docs = self._agent.get_documents(self._course)
        # 分组
        groups = {"textbook": "▪ 教材", "past_paper": "▪ 真题"}
        grouped = {k: [] for k in groups}
        for d in docs:
            t = d.get("doc_type", "textbook")
            grouped.get(t, grouped["textbook"]).append(d)
        for key, label in groups.items():
            items = grouped.get(key, [])
            if not items:
                continue
            group = QTreeWidgetItem(self.tree, [label])
            group.setExpanded(True)
            group.setFlags(group.flags() & ~Qt.ItemIsSelectable)
            for d in items:
                item = QTreeWidgetItem(group, [f"  {d['filename']}"])
                item.setData(0, Qt.UserRole, d["filename"])
        # 计划
        plans = self._agent.get_plans()
        if plans:
            plan_group = QTreeWidgetItem(self.tree, ["📋 计划"])
            plan_group.setExpanded(True)
            plan_group.setFlags(plan_group.flags() & ~Qt.ItemIsSelectable)
            for p in plans:
                item = QTreeWidgetItem(plan_group, [f"  {p['display_name']}"])
                item.setData(0, Qt.UserRole, f"__plan__:{p['filename']}")
        if not docs and not plans:
            item = QTreeWidgetItem(self.tree, ["📚 暂无文档"])
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
        self.tree.expandAll()

    def _context_menu(self, pos):
        item = self.tree.itemAt(pos)
        if not item or not item.parent():
            return
        fn = item.data(0, Qt.UserRole)
        if not fn:
            return
        menu = QMenu(self)
        delete = menu.addAction("🗑️ 删除")
        if menu.exec(self.tree.viewport().mapToGlobal(pos)) == delete:
            if fn.startswith("__plan__:"):
                # 删除计划文件
                pfn = fn.split(":", 1)[1]
                path = self._agent.PLANS_DIR / pfn
                if path.exists():
                    path.unlink()
            else:
                if QMessageBox.question(self, "确认", f"删除「{fn}」？", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
                    self._agent.delete_document(fn)
            self._refresh()

    def mouseDoubleClickEvent(self, event):
        item = self.tree.currentItem()
        if not item or not item.parent():
            return
        fn = item.data(0, Qt.UserRole)
        if not fn:
            return
        if fn.startswith("__plan__:"):
            pfn = fn.split(":", 1)[1]
            content = self._agent.get_plan_content(pfn)
            if content:
                from frontend.components.preview_dialog import DocumentPreviewDialog
                dialog = DocumentPreviewDialog(title=pfn, text=content, size=len(content), parent=self)
                dialog.exec()
        elif self._agent._sources.get(fn):
            result = self._agent.preview_document(fn)
            if result.get("ok"):
                from frontend.components.preview_dialog import DocumentPreviewDialog
                dialog = DocumentPreviewDialog(
                    title=result.get("filename", fn),
                    text=result.get("text", ""),
                    size=result.get("size", 0),
                    scanned=result.get("scanned", False),
                    parent=self,
                )
                dialog.exec()
