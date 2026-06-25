"""
模型下载线程 — ModelDownloadThread (QThread 子类)

直接继承 QThread 并重写 run()，比 QObject+moveToThread 更可靠。
通过信号报告进度，不阻塞主线程 UI。
"""
from __future__ import annotations

import os
import time
from pathlib import Path

from loguru import logger
from PySide6.QtCore import QThread, Signal

from backend.config import settings
from backend.model_checker import _model_folder


class DownloadProgress:
    """下载进度快照。"""
    def __init__(self, model_name: str = "") -> None:
        self.model_name = model_name
        self.current_file = ""
        self.file_index = 0
        self.total_files = 0
        self.bytes_downloaded = 0
        self.total_bytes = 0
        self.speed_kbps: float = 0.0
        self.elapsed_sec: float = 0.0

    @property
    def percent(self) -> float:
        if self.total_bytes <= 0:
            return 0.0
        return min(self.bytes_downloaded / self.total_bytes * 100, 100.0)

    @property
    def label(self) -> str:
        return f"正在下载 {self.model_name} ({self.percent:.0f}%)"


class ModelDownloadThread(QThread):
    """★ QThread 子类 — 模型下载（不阻塞主线程）。

    信号:
        progress(DownloadProgress) — 进度更新
        model_done(str)            — 单个模型完成
        model_error(str, str)      — 单个模型失败 (模型名, 原因)
        all_done()                 — 全部完成
    """

    progress = Signal(DownloadProgress)
    model_done = Signal(str)
    model_error = Signal(str, str)
    all_done = Signal()

    def __init__(self, model_names: list[str], parent=None) -> None:
        super().__init__(parent)
        self.model_names = model_names

    def run(self) -> None:
        """★ 在线程中执行下载（run() 在 QThread.start() 后自动在新线程运行）。"""
        from huggingface_hub import HfApi
        from requests.exceptions import RequestException

        api = HfApi()

        for name in self.model_names:
            model_id = self._model_id(name)
            if model_id is None:
                self.model_error.emit(name, "未知模型类型")
                continue

            try:
                self._download_model(api, name, model_id)
                self.model_done.emit(name)
            except (RequestException, OSError, Exception) as e:
                logger.opt(exception=True).error("模型下载失败: {} — {}", name, e)
                self.model_error.emit(name, str(e)[:100])

        self.all_done.emit()

    # ── 内部下载 ──────────────────────────────

    def _download_model(self, api: "HfApi", name: str, repo_id: str) -> None:
        from huggingface_hub import hf_hub_download

        models_dir = settings.models_dir
        models_dir.mkdir(parents=True, exist_ok=True)
        local_dir = models_dir / _model_folder(repo_id)
        local_dir.mkdir(parents=True, exist_ok=True)

        logger.info("开始下载模型: {} → {}", repo_id, local_dir)

        old_offline = os.environ.get("HF_HUB_OFFLINE")
        os.environ["HF_HUB_OFFLINE"] = "0"

        try:
            repo_info = api.repo_info(repo_id, files_metadata=True)
            siblings = list(repo_info.siblings or [])
            files = [s for s in siblings if s.size is not None and s.size > 0]

            if not files:
                return

            total = sum(s.size for s in files)
            downloaded = 0
            prog = DownloadProgress(name)
            prog.total_files = len(files)
            prog.total_bytes = total
            start = time.time()

            for idx, sibling in enumerate(files):
                fp = sibling.rfilename
                local_f = local_dir / fp
                local_f.parent.mkdir(parents=True, exist_ok=True)

                if local_f.exists() and local_f.stat().st_size == sibling.size:
                    downloaded += sibling.size
                else:
                    hf_hub_download(
                        repo_id=repo_id, filename=fp,
                        local_dir=str(local_dir),
                        local_dir_use_symlinks=False,
                        resume_download=True, token=None,
                    )
                    downloaded += local_f.stat().st_size if local_f.exists() else sibling.size

                prog.bytes_downloaded = min(downloaded, total)
                prog.file_index = idx + 1
                prog.current_file = fp
                elapsed = time.time() - start
                prog.elapsed_sec = elapsed
                prog.speed_kbps = (downloaded / 1024) / (elapsed or 0.001)
                self.progress.emit(prog)

        finally:
            if old_offline is not None:
                os.environ["HF_HUB_OFFLINE"] = old_offline
            else:
                os.environ.pop("HF_HUB_OFFLINE", None)

        logger.info("模型下载完成: {} ({:.1f} MB)", repo_id, total / 1024 / 1024)

    @staticmethod
    def _model_id(name: str) -> str | None:
        if name == "embedding":
            return settings.embedding_model
        elif name == "reranker":
            return settings.reranker_model
        return None
