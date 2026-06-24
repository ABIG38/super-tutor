"""
设置对话框 — API Key / Base / 模型名 / 存储目录。

配置保存到 .env 文件，立即生效。
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QDialogButtonBox,
    QMessageBox,
)


ENV_PATH = Path(".env")


class SettingsDialog(QDialog):
    """设置对话框。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ 设置")
        self.setMinimumWidth(450)
        self._setup_ui()
        self._load_env()

    def _setup_ui(self) -> None:
        """构建表单。"""
        layout = QVBoxLayout(self)

        form = QFormLayout()
        form.setSpacing(10)

        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("sk-...")
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        form.addRow("API Key:", self.api_key_edit)

        self.api_base_edit = QLineEdit()
        self.api_base_edit.setPlaceholderText("https://api.deepseek.com/v1")
        form.addRow("API Base:", self.api_base_edit)

        self.model_edit = QLineEdit()
        self.model_edit.setPlaceholderText("deepseek-chat")
        form.addRow("模型:", self.model_edit)

        self.storage_edit = QLineEdit()
        self.storage_edit.setPlaceholderText("knowledge_base")
        form.addRow("存储目录:", self.storage_edit)

        layout.addLayout(form)

        # 按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save_env)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_env(self) -> None:
        """从 .env 加载当前配置。"""
        if not ENV_PATH.exists():
            return
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip("\"'")
            if key == "OPENAI_API_KEY":
                self.api_key_edit.setText(val)
            elif key == "OPENAI_BASE_URL":
                self.api_base_edit.setText(val)
            elif key == "OPENAI_MODEL":
                self.model_edit.setText(val)
            elif key == "STORAGE_ROOT":
                self.storage_edit.setText(val)

    def _save_env(self) -> None:
        """保存配置到 .env。"""
        api_key = self.api_key_edit.text().strip()
        if not api_key:
            QMessageBox.warning(self, "提示", "API Key 不能为空")
            return

        lines = [
            f'OPENAI_API_KEY={api_key}',
            f'OPENAI_BASE_URL={self.api_base_edit.text().strip() or "https://api.deepseek.com/v1"}',
            f'OPENAI_MODEL={self.model_edit.text().strip() or "deepseek-chat"}',
            f'STORAGE_ROOT={self.storage_edit.text().strip() or "knowledge_base"}',
            "",
        ]
        ENV_PATH.write_text("\n".join(lines), encoding="utf-8")
        QMessageBox.information(self, "✅", "配置已保存，重启后生效")
        self.accept()
