"""
学习追踪器 — SQLite 进度持久化 + 并发安全 + 损坏恢复。

对应 TECH_DESIGN.md §2.5, §9 #㉑ #㉒。
"""
import sqlite3
import os
import time
import shutil
from pathlib import Path
from typing import List, Dict

from loguru import logger

from backend.config import settings


class StudyTracker:
    """SQLite-based learning progress tracker.

    边界处理:
        - ㉑ SQLite 损坏 → 自动备份 .corrupt → 重建
        - ㉒ 并发写入 → WAL + retry_on_busy (3次×50ms)
    """

    MAX_RETRIES = 3
    RETRY_DELAY = 0.05  # 50ms

    def __init__(self, db_path: str | None = None):
        if db_path:
            self.db_path = Path(db_path)
        else:
            self.db_path = settings.tracker_db
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    # ── 连接管理 ──────────────────────────────────────

    def _get_conn(self) -> sqlite3.Connection:
        """获取连接 — WAL 模式 + busy timeout。"""
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")  # 5s
        return conn

    def _execute_with_retry(self, sql: str, params: tuple = ()) -> None:
        """★ ㉒：带重试的写入操作 (retry_on_busy)。"""
        last_error = None
        for attempt in range(self.MAX_RETRIES):
            try:
                with self._get_conn() as conn:
                    conn.execute(sql, params)
                return
            except sqlite3.OperationalError as e:
                last_error = e
                if "database is locked" in str(e).lower() and attempt < self.MAX_RETRIES - 1:
                    logger.debug("SQLite 锁定，重试 {}/{}", attempt + 1, self.MAX_RETRIES)
                    time.sleep(self.RETRY_DELAY)
                else:
                    raise
        raise RuntimeError(f"SQLite 写入失败（已重试{self.MAX_RETRIES}次）") from last_error

    # ── 初始化 + 损坏恢复 ────────────────────────────

    def _init_db(self) -> None:
        """初始化数据库 — 含 SQLite 损坏自动恢复。"""
        try:
            with self._get_conn() as conn:
                conn.execute('''
                CREATE TABLE IF NOT EXISTS daily_task (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plan_id TEXT NOT NULL,
                    course TEXT DEFAULT '',
                    day_index INTEGER NOT NULL,
                    task_content TEXT NOT NULL,
                    completed INTEGER DEFAULT 0,
                    updated_at TEXT DEFAULT (datetime('now'))
                )
                ''')
            logger.info("学习进度数据库就绪: {}", self.db_path)

        except (sqlite3.DatabaseError, sqlite3.OperationalError) as e:
            # ★ ㉑：数据库损坏 — 备份 + 重建
            logger.warning("数据库损坏检测: {} — {}", self.db_path, e)
            self._recover_db()
            # 递归重试一次
            with self._get_conn() as conn:
                conn.execute('''
                CREATE TABLE IF NOT EXISTS daily_task (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plan_id TEXT NOT NULL,
                    course TEXT DEFAULT '',
                    day_index INTEGER NOT NULL,
                    task_content TEXT NOT NULL,
                    completed INTEGER DEFAULT 0,
                    updated_at TEXT DEFAULT (datetime('now'))
                )
                ''')
            logger.info("数据库已重建: {}", self.db_path)

    def _recover_db(self) -> None:
        """备份损坏的数据库文件为 .corrupt 后缀。"""
        if not self.db_path.exists():
            return
        backup = self.db_path.with_suffix(".db.corrupt")
        try:
            shutil.copy2(self.db_path, backup)
            logger.warning("已备份损坏数据库: {}", backup)
        except Exception as e:
            logger.error("备份损坏数据库失败: {}", e)
        try:
            self.db_path.unlink()
        except Exception as e:
            logger.error("删除损坏数据库失败: {}", e)

    # ── 计划管理 ──────────────────────────────────────

    def init_plan(self, plan_id: str, tasks: List[Dict], course: str = "") -> None:
        """Init a new plan with daily tasks."""
        with self._get_conn() as conn:
            if course:
                conn.execute("DELETE FROM daily_task WHERE course = ?", (course,))
            for task in tasks:
                conn.execute(
                    "INSERT INTO daily_task (plan_id, course, day_index, task_content, completed) "
                    "VALUES (?, ?, ?, ?, 0)",
                    (plan_id, course, task.get("day", 1), task.get("task", "")),
                )

    def mark_task(self, task_id: int, completed: bool) -> None:
        """Mark a specific task as completed/uncompleted (带重试)。"""
        self._execute_with_retry(
            "UPDATE daily_task SET completed = ?, updated_at = datetime('now') WHERE id = ?",
            (1 if completed else 0, task_id),
        )

    def get_plan_progress(self, course: str = "") -> Dict:
        """Get the current progress for the active plan in the course."""
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*), SUM(completed) FROM daily_task WHERE course = ?",
                (course,),
            )
            row = cursor.fetchone()
            total = row[0] or 0
            completed = row[1] or 0

            tasks_cursor = conn.execute(
                "SELECT id, day_index, task_content, completed FROM daily_task "
                "WHERE course = ? ORDER BY day_index, id",
                (course,),
            )
            tasks = [
                {"id": r[0], "day": r[1], "task": r[2], "completed": bool(r[3])}
                for r in tasks_cursor.fetchall()
            ]

            return {
                "total": total,
                "completed": completed,
                "pct": (completed / total) if total > 0 else 0.0,
                "tasks": tasks,
            }

    def get_completed_chapters(self, course: str = "") -> List[str]:
        """Get list of completed task contents for prompt injection."""
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT task_content FROM daily_task WHERE course = ? AND completed = 1",
                (course,),
            )
            return [r[0] for r in cursor.fetchall()]

    def delete_course(self, course: str) -> None:
        with self._get_conn() as conn:
            conn.execute("DELETE FROM daily_task WHERE course = ?", (course,))
        logger.info("已删除课程 {} 的所有进度数据", course)

    def close(self) -> None:
        """关闭连接（SQLite context manager 已自动处理）。"""
        pass
