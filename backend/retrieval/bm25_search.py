"""
BM25 关键词检索引擎 — 精简版。
"""
from __future__ import annotations

import pickle
import tempfile
from pathlib import Path
from typing import List, Dict

import jieba
from loguru import logger
from rank_bm25 import BM25Okapi

from backend.config import settings


class BM25Searcher:
    def __init__(self):
        self._corpus_path = Path(str(settings.storage_root_path) + "/index/bm25_corpus.pkl")
        self._corpus: List[Dict] = []
        self._index: BM25Okapi | None = None
        self._load()

    def add_chunks(self, chunks: List[Dict]) -> None:
        """增量追加 chunks。"""
        if not chunks:
            return
        new_tokens = []
        for c in chunks:
            content = c.get("content", "")
            meta = c.get("metadata", {})
            cid = f"{meta.get('filename','')}_{meta.get('chunk_index',0)}"
            if any(item["id"] == cid for item in self._corpus):
                continue
            tokens = [t for t in jieba.lcut(content) if len(t.strip()) > 0]
            if tokens:
                self._corpus.append({"id": cid, "tokens": tokens, "meta": meta})
                new_tokens.append(tokens)
        if not new_tokens:
            return
        all_t = [item["tokens"] for item in self._corpus if item["tokens"]]
        self._index = BM25Okapi(all_t) if all_t else None
        logger.info("BM25 索引: {} chunks", len(self._corpus))

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        if self._index is None:
            return []
        tokens = [t for t in jieba.lcut(query) if len(t.strip()) > 0]
        if not tokens:
            return []
        scores = self._index.get_scores(tokens)
        if not scores.any():
            return []
        indexed = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        results = []
        for idx, score in indexed:
            if len(results) >= top_k:
                break
            item = self._corpus[idx]
            meta = item["meta"]
            results.append({
                "content": "",  # 需从 vector 结果补齐
                "filename": meta.get("filename", ""),
                "course": meta.get("course", ""),
                "score": float(score),
                "source": "bm25",
            })
        return results

    def save(self) -> None:
        if not self._corpus:
            return
        self._corpus_path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(suffix=".pkl", prefix="bm25_", dir=str(self._corpus_path.parent))
        try:
            with open(fd, "wb") as f:
                pickle.dump(self._corpus, f)
            Path(tmp).replace(self._corpus_path)
        except Exception:
            Path(tmp).unlink(missing_ok=True)

    def _load(self) -> None:
        if not self._corpus_path.exists():
            return
        try:
            self._corpus = pickle.loads(self._corpus_path.read_bytes())
            tokenized = [item["tokens"] for item in self._corpus if item["tokens"]]
            if tokenized:
                self._index = BM25Okapi(tokenized)
        except Exception:
            self._corpus = []
