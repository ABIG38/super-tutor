"""
知识库文档树 — 左侧面板。

按课程显示已索引的文档列表，按「教材」和「真题」分组。
支持上传、删除、重命名。
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTreeWidget,
    QTreeWidgetItem,
    QPushButton,
    QHeaderView,
    QFileDialog,
    QMessageBox,
    QMenu,
)


class DocumentTree(QWidget):
    """知识库文档树组件。

    左侧面板，显示当前课程的文档列表。
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """构建 UI。"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # 文档树
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(16)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.tree)

        # 上传按钮
        self.btn_upload = QPushButton("📄 上传文档")
        self.btn_upload.clicked.connect(self._upload_document)
        layout.addWidget(self.btn_upload)

        # 初始占位
        self._show_empty_state()

    def _show_empty_state(self) -> None:
        """空状态提示。"""
        self.tree.clear()
        item = QTreeWidgetItem(self.tree, ["📚 暂无文档"])
        item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
        self.tree.addTopLevelItem(item)

    def _upload_document(self) -> None:
        """弹出文件选择对话框。"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择文档",
            "",
            "文档 (*.pdf *.docx *.md *.txt);;所有文件 (*)",
        )
        if files:
            for f in files:
                self._add_document_item(f)

    def _add_document_item(self, file_path: str) -> None:
        """向树中添加一个文档项。"""
        from pathlib import Path
        path = Path(file_path)
        name = path.name
        ext = path.suffix.lower()

        # 确定分组
        group_name = "📖 教材"
        # 找到或创建分组节点
        group_item = None
        for i in range(self.tree.topLevelItemCount()):
            if self.tree.topLevelItem(i).text(0).startswith(group_name):
                group_item = self.tree.topLevelItem(i)
                break

        if group_item is None:
            group_item = QTreeWidgetItem(self.tree, [group_name])
            group_item.setExpanded(True)

        doc_item = QTreeWidgetItem(group_item, [f"📄 {name}"])
        doc_item.setData(0, Qt.UserRole, file_path)
        self.tree.expandAll()

    def _show_context_menu(self, pos) -> None:
        """右键菜单。"""
        item = self.tree.itemAt(pos)
        if item is None or item.parent() is None:
            return  # 只在文档项上显示菜单

        menu = QMenu(self)
        rename_action = menu.addAction("✏️ 重命名")
        delete_action = menu.addAction("🗑️ 删除")

        action = menu.exec(self.tree.viewport().mapToGlobal(pos))
        if action == rename_action:
            self._rename_document(item)
        elif action == delete_action:
            self._delete_document(item)

    def _rename_document(self, item: QTreeWidgetItem) -> None:
        """重命名文档。"""
        from PySide6.QtWidgets import QInputDialog
        old_name = item.text(0).replace("📄 ", "")
        new_name, ok = QInputDialog.getText(self, "重命名", "新文件名：", text=old_name)
        if ok and new_name.strip():
            item.setText(0, f"📄 {new_name.strip()}")

    def _delete_document(self, item: QTreeWidgetItem) -> None:
        """删除文档。"""
        name = item.text(0).replace("📄 ", "")
        confirm = QMessageBox.question(
            self, "删除文档", f"确定删除「{name}」吗？",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            parent = item.parent()
            if parent:
                parent.removeChild(item)
