"""LLM 集成模块 — CitationLLM 强制溯源客户端。"""

from .client import CITATION_SYSTEM_PROMPT, ChunkForLLM, CitationLLM, LLMError

__all__ = [
    "CITATION_SYSTEM_PROMPT",
    "ChunkForLLM",
    "CitationLLM",
    "LLMError",
]
