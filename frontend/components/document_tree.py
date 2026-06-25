"""知识库文档树 — 精简版，双击预览文件/计划。"""
from __future__ import annotations
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTreeWidget, QTreeWidgetItem, QPushButton, QFileDialog, QMessageBox, QMenu)


class DocumentTree(QWidget):
    def __init__(self, agent, parent=None):
        super().__init__(parent)
        self._agent = agent
        self._course = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self); layout.setContentsMargins(0, 0, 0, 0)
        h = QWidget(); h.setFixedHeight(48)
        h.setStyleSheet("background-color:#050505;border-bottom:1px solid #1f1f22")
        hl = QHBoxLayout(h); hl.setContentsMargins(20,0,20,0)
        t = QLabel("知识库"); t.setStyleSheet("color:#a0a0a5;font-size:11px;font-weight:700;letter-spacing:2px")
        hl.addWidget(t)
        self.btn_upload = QPushButton("+ 添加")
        self.btn_upload.setFixedSize(56,24)
        self.btn_upload.setStyleSheet("QPushButton{background:transparent;color:#ccff00;border:1px solid #ccff00;border-radius:4px;font-size:10px;font-weight:700}QPushButton:hover{background-color:#ccff00;color:#050505}")
        self.btn_upload.clicked.connect(self._upload)
        hl.addWidget(self.btn_upload); layout.addWidget(h)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True); self.tree.setIndentation(12)
        self.tree.setStyleSheet("QTreeWidget{background-color:#0f0f11;color:#a0a0a5;border:none;font-size:12px;padding:12px 8px}QTreeWidget::item{padding:8px 12px;border-radius:4px}QTreeWidget::item:hover{background-color:#1a1a1d;color:#fcfcfc}QTreeWidget::item:selected{background-color:#ccff0015;color:#ccff00;border-left:2px solid #ccff00}")
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._context_menu)
        self.tree.itemDoubleClicked.connect(self._on_double_click)
        layout.addWidget(self.tree); self._refresh()

    def _upload(self):
        files, _ = QFileDialog.getOpenFileNames(self, "选择文档", "", "文档 (*.pdf *.docx *.md *.txt);;所有文件 (*)")
        for f in files:
            p = Path(f)
            r = self._agent.ingest_document(str(p), course=self._course)
            if r.get("ok"): self._refresh()
            elif r.get("reason") == "duplicate":
                if QMessageBox.question(self, "重复", f"「{p.name}」已存在，覆盖？", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
                    self._agent.delete_document(p.name)
                    self._agent.ingest_document(str(p), course=self._course)
                    self._refresh()
            else: QMessageBox.warning(self, "错误", f"「{p.name}」: {r.get('reason','?')}")

    def _on_double_click(self, item, _col):
        """★ 双击预览文档/计划。"""
        fn = item.data(0, Qt.UserRole)
        if not fn or not item.parent():
            return
        from frontend.components.preview_dialog import DocumentPreviewDialog
        if fn.startswith("__plan__:"):
            pfn = fn.split(":", 1)[1]
            content = self._agent.get_plan_content(pfn)
            if content:
                d = DocumentPreviewDialog(title=pfn, text=content, size=len(content), parent=self)
                d.exec()
        elif self._agent._sources.get(fn):
            r = self._agent.preview_document(fn)
            if r.get("ok"):
                d = DocumentPreviewDialog(title=r.get("filename",fn), text=r.get("text",""),
                    size=r.get("size",0), scanned=r.get("scanned",False), parent=self)
                d.exec()

    def _refresh(self):
        self.tree.clear()
        docs = self._agent.get_documents(self._course)
        groups = {"textbook":"▪ 教材","past_paper":"▪ 真题"}
        gd = {k:[] for k in groups}
        for d in docs:
            t = d.get("doc_type","textbook")
            gd.get(t,gd["textbook"]).append(d)
        for k,lbl in groups.items():
            if not gd[k]: continue
            g = QTreeWidgetItem(self.tree,[lbl]); g.setExpanded(True)
            g.setFlags(g.flags() & ~Qt.ItemIsSelectable)
            for d in gd[k]:
                it = QTreeWidgetItem(g,[f"  {d['filename']}"])
                it.setData(0, Qt.UserRole, d["filename"])
        plans = self._agent.get_plans()
        if plans:
            pg = QTreeWidgetItem(self.tree,["📋 计划"]); pg.setExpanded(True)
            pg.setFlags(pg.flags() & ~Qt.ItemIsSelectable)
            for p in plans:
                it = QTreeWidgetItem(pg,[f"  {p['display_name']}"])
                it.setData(0, Qt.UserRole, f"__plan__:{p['filename']}")
        if not docs and not plans:
            it = QTreeWidgetItem(self.tree,["📚 暂无文档"])
            it.setFlags(it.flags() & ~Qt.ItemIsSelectable)
        self.tree.expandAll()

    def _context_menu(self, pos):
        item = self.tree.itemAt(pos)
        if not item or not item.parent(): return
        fn = item.data(0, Qt.UserRole)
        if not fn: return
        menu = QMenu(self)
        delete = menu.addAction("🗑️ 删除")
        if menu.exec(self.tree.viewport().mapToGlobal(pos)) == delete:
            if fn.startswith("__plan__:"):
                pfn = fn.split(":",1)[1]
                p = self._agent.PLANS_DIR / pfn
                if p.exists(): p.unlink()
            else:
                if QMessageBox.question(self,"确认",f"删除「{fn}」？",QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
                    self._agent.delete_document(fn)
            self._refresh()
