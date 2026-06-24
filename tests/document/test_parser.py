"""
单元测试 — DocumentParser

覆盖场景（对应 TECH_DESIGN.md 第 9 节）:
    - ① 扫描版 PDF → scanned=True
    - ② 加密 PDF → PermissionError
    - ③ 文件 >200MB → ValueError
    - 正常 PDF / DOCX / MD / TXT 解析
    - 扩展名不支持 → ValueError
    - 文件不存在 → FileNotFoundError

使用 unittest.mock 模拟外部依赖（fitz.open、DocxDocument、pathlib.Path 等）。
"""

from __future__ import annotations

import pathlib
from unittest.mock import MagicMock, mock_open, patch

import pytest

from backend.document.parser import DocumentParser, ParsedDocument


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def parser() -> DocumentParser:
    """返回一个干净的 DocumentParser 实例。"""
    return DocumentParser()


# ── 正常解析测试 ────────────────────────────────────────────────────────────


class TestParseNormal:
    """正常文档解析路径。"""

    # TODO: 实现正常 PDF 解析测试
    # TODO: 实现正常 DOCX 解析测试
    # TODO: 实现正常 MD/TXT 解析测试
    pass


# ── 边界情况测试 ────────────────────────────────────────────────────────────


class TestParseEdgeCases:
    """TECH_DESIGN.md 第 9 节边界情况。"""

    # TODO: ① 扫描版 PDF — mock fitz 返回空文本
    # TODO: ② 加密 PDF — mock fitz 抛加密异常
    # TODO: ③ 文件 >200MB — mock stat().st_size 返回 201MB
    # TODO: 扩展名不支持 — 传入 .xyz 文件
    # TODO: 文件不存在 — 传入不存在路径
    pass


# ── ParsedDocument 模型测试 ─────────────────────────────────────────────────


class TestParsedDocument:
    """Pydantic 模型校验。"""

    def test_default_values(self) -> None:
        """验证默认值正确。"""
        doc = ParsedDocument(text="hello", filename="test.pdf", extension=".pdf")
        assert doc.page_count == 0
        assert doc.size_bytes == 0
        assert doc.scanned is False
        assert doc.doc_type == "textbook"

    def test_requires_required_fields(self) -> None:
        """验证必填字段不可缺失。"""
        with pytest.raises(Exception):
            ParsedDocument()  # type: ignore[call-arg]
