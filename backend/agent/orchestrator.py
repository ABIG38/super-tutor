"""
Orchestrator — 精简版：只做上传→索引→检索→LLM 流式回答。
"""
from __future__ import annotations

import uuid
import threading
from pathlib import Path
from typing import List, Dict, Literal, Generator

from loguru import logger
from dotenv import load_dotenv

from backend.config import settings
from backend.document.parser import DocumentParser
from backend.document.splitter import chunk_document
from backend.retrieval.vector_store import VectorStore
from backend.retrieval.bm25_search import BM25Searcher
from backend.llm.client import CitationLLM, ChunkForLLM


class SuperTutorAgent:
    """单例 — 文档解析 + 向量检索 + LLM 流式问答。"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if not cls._instance:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "initialized") and self.initialized:
            return
        load_dotenv()

        self.parser = DocumentParser()
        self.vector_store = VectorStore()
        self.bm25 = BM25Searcher()

        api_key = settings.llm_api_key if settings.llm_api_key != "MISSING_KEY" else __import__("os").environ.get("OPENAI_API_KEY", "")
        self.llm = CitationLLM(
            api_key=api_key,
            api_base=settings.llm_api_base,
            model=settings.llm_model,
        )

        # 来源追踪 — 从 ChromaDB 恢复
        self._sources: Dict[str, dict] = {}
        self._restore_sources()
        self.initialized = True

    def _restore_sources(self) -> None:
        try:
            for fn, info in self.vector_store.get_source_files().items():
                self._sources[fn] = {
                    "doc_type": info.get("doc_type", "textbook"),
                    "course": info.get("course", ""),
                }
        except Exception:
            pass

    # ── 文档管理 ──────────────────────────────────

    def ingest_document(self, file_path: str, course: str = "") -> Dict:
        path = Path(file_path)
        fn = path.name
        if fn in self._sources:
            return {"ok": False, "reason": "duplicate", "filename": fn}
        try:
            doc = self.parser.parse(file_path, course=course)
            if doc.scanned:
                return {"ok": False, "reason": "scanned_pdf", "filename": fn}
            chunks = chunk_document(doc.text, {"filename": doc.filename, "course": course})
            self.vector_store.add_chunks(chunks)
            self.bm25.add_chunks(chunks)  # ★ F-09: 同步 BM25
            self._sources[fn] = {"doc_type": doc.doc_type, "course": course}
            return {"ok": True, "chunk_count": len(chunks), "filename": fn}
        except (FileNotFoundError, ValueError, PermissionError) as e:
            return {"ok": False, "reason": str(e)[:100], "filename": fn}
        except Exception as e:
            logger.opt(exception=True).error("索引异常: {}", e)
            return {"ok": False, "reason": str(e)[:100], "filename": fn}

    def delete_document(self, filename: str) -> Dict:
        if filename not in self._sources:
            return {"ok": False, "reason": "not_found"}
        try:
            self.vector_store.delete_by_source(filename)
            self._sources.pop(filename, None)
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "reason": str(e)}

    def get_documents(self, course: str = "") -> List[Dict]:
        return [{"filename": fn, **info} for fn, info in self._sources.items()
                if not course or info.get("course") == course]

    def preview_document(self, filename: str) -> Dict:
        return {"ok": False, "reason": "预览暂不支持"}  # 精简版暂不实现

    # ── 问答 ──────────────────────────────────────

    def ask(self, query: str, course: str = "") -> Generator[str, None, None]:
        if not self._sources:
            yield "知识库为空，请先上传文档。"
            return
        filter_meta = {"course": course} if course else None
        # ★ F-09: 混合检索 — 向量 + BM25
        vec_chunks = self.vector_store.search(query, top_k=5, filter_meta=filter_meta)
        bm25_chunks = self.bm25.search(query, top_k=5)
        # 补齐 BM25 结果的 content
        for b in bm25_chunks:
            for v in vec_chunks:
                if b.get("filename") == v.get("filename"):
                    b["content"] = v.get("content", "")
                    break
        # 融合：去重合并
        seen = set()
        all_chunks = []
        for c in vec_chunks + bm25_chunks:
            key = c.get("content", "")[:80]
            if key and key not in seen:
                seen.add(key)
                all_chunks.append(c)
        if not all_chunks:
            yield "未在上传文档中找到相关答案，请检查文档内容或更换提问方式。"
            return
        llm_chunks = [
            ChunkForLLM(content=c.get("content",""), filename=c.get("filename",""), course=c.get("course",""), score=c.get("score",0))
            for c in all_chunks[:7]
        ]
        for token in self.llm.generate_with_citation_stream(query, llm_chunks):
            yield token

    def cancel_stream(self) -> None:
        self.llm.cancel_stream()

    # ── 会话管理 ──────────────────────────────────

    def chat_new(self, name: str = "") -> Dict:
        import backend.chat_store as cs
        return cs.new_session(name)

    def chat_list(self) -> List[Dict]:
        import backend.chat_store as cs
        return cs.list_sessions()

    def chat_delete(self, session_id: str) -> None:
        import backend.chat_store as cs
        cs.delete_session(session_id)

    def chat_rename(self, session_id: str, name: str) -> None:
        import backend.chat_store as cs
        cs.rename_session(session_id, name)

    def chat_messages(self, session_id: str) -> List[Dict]:
        import backend.chat_store as cs
        return cs.load_messages(session_id)

    def chat_append(self, session_id: str, role: str, content: str) -> None:
        import backend.chat_store as cs
        cs.append_message(session_id, role, content)

    # ── 计划生成 ──────────────────────────────────

    def generate_plan(self, days: int = 30, hours: int = 2, course: str = "") -> str:
        """让 AI 根据教材上下文生成复习计划。"""
        # 检索教材内容作为 chunks（让 CitationLLM 自动注入 <context>）
        chunks = self.vector_store.search("章节目录 章节 重点", top_k=15, filter_meta={"course": course} if course else None)
        if not chunks:
            return "请先上传教材再生成计划。"

        llm_chunks = [
            ChunkForLLM(content=c.get("content",""), filename=c.get("filename",""), course=c.get("course",""))
            for c in chunks
        ]

        prompt = (
            f"你是一位资深考研规划师。请根据上方<context>教材内容，"
            f"为我制定一份 {days} 天的学习计划，每天学习 {hours} 小时。\n\n"
            "要求：\n"
            "1. 按天拆分，每天安排具体章节内容\n"
            "2. 优先覆盖重点章节\n"
            "3. Markdown 格式\n"
            "4. 如果教材内容不足，说明缺少什么信息"
        )

        try:
            result = self.llm.generate_with_citation(
                query=prompt, chunks=llm_chunks, timeout=60,
            )
            return result
        except Exception as e:
            logger.error("计划生成失败: {}", e)
            return f"计划生成失败：{e}"
