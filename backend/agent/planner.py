"""
学习计划生成器 — StudyPlanner

调用 LLM 基于教材内容生成 JSON 格式复习计划。
包含健壮的 JSON 提取逻辑，应对 LLM 输出格式不一致。
"""
from typing import List, Dict, Union
import json
import re
from loguru import logger

from backend.llm.client import ChunkForLLM


class PlanGenerationError(Exception):
    def __init__(self, message: str, detail: str = "", original: Exception | None = None) -> None:
        super().__init__(message)
        self.detail = detail
        self.original = original


class StudyPlanner:
    """Generates study plans using LLM."""

    def __init__(self, llm):
        self.llm = llm

    def generate_plan_json(
        self,
        days: int,
        hours: int,
        context_chunks: List[Union[Dict, ChunkForLLM]],
        completed_chapters: List[str] | None = None,
    ) -> List[Dict]:
        """
        Generate a study plan and return it as a list of dictionaries.

        Raises:
            PlanGenerationError: 无教材 / LLM 返回异常 / JSON 解析失败。
        """
        # ★ 检查是否有教材内容
        llm_chunks = self._normalize_chunks(context_chunks)
        has_content = any(c.content.strip() for c in llm_chunks)

        if not has_content:
            raise PlanGenerationError(
                "知识库中没有教材内容",
                detail="请先上传含目录的教材文件后再生成计划",
            )

        completed_str = "\n".join(completed_chapters) if completed_chapters else "无"

        # ★ 清洁的 prompt（无缩进 whitespace）
        prompt_lines = [
            "你是一位资深考研规划师。请根据下方<context>参考资料，为我制定一个"
            + str(days) + "天的学习计划，每天学习" + str(hours) + "小时。",
            "",
            "【硬性约束】",
            "1. 只能基于提供的参考资料生成计划。",
            "2. 跳过我已掌握的内容：" + completed_str,
            "3. 必须输出为纯 JSON 格式（List of Objects），不要任何其他 Markdown 文本、不要代码块标记、不要解释！",
            "4. 格式示例：" + '[{"day": 1, "task": "第一章 绪论 - 数据结构概念"}, {"day": 2, "task": "第二章 线性表 - 顺序表"}]',
            "",
            "请直接输出 JSON 数组，以 [ 开头，以 ] 结尾。",
        ]
        prompt = "\n".join(prompt_lines)

        try:
            logger.info("规划生成: {}天 {}小时/天, chunks={}", days, hours, len(llm_chunks))
            raw_response = self.llm.generate_with_citation(
                query=prompt, chunks=llm_chunks, timeout=60,
            )

            # ★ 健壮的 JSON 提取
            plan_data = self._extract_json(raw_response)

            if not isinstance(plan_data, list) or len(plan_data) == 0:
                raise PlanGenerationError(
                    "AI 返回的计划为空", detail=raw_response[:200],
                )

            # 校验每个条目有 day 和 task
            for item in plan_data:
                if not isinstance(item, dict) or "day" not in item or "task" not in item:
                    logger.warning("计划条目格式异常: {}", item)

            logger.info("计划生成成功: {} 天", len(plan_data))
            return plan_data

        except PlanGenerationError:
            raise

        except json.JSONDecodeError as e:
            logger.error("JSON 解析失败: {} — raw: {}", e, raw_response[:300])
            raise PlanGenerationError(
                "AI 返回的计划格式异常，请调整参数后重新生成",
                detail=_truncate(raw_response, 300),
                original=e,
            ) from e

        except Exception as e:
            logger.opt(exception=True).error("规划生成异常: {}", e)
            raise PlanGenerationError(
                "计划生成失败，请检查网络连接或稍后重试",
                detail=str(e)[:200],
                original=e,
            ) from e

    # ── 内部 ────────────────────────────────────

    @staticmethod
    def _extract_json(text: str) -> list:
        """★ 健壮的 JSON 提取 — 应对 LLM 输出的各种格式漂移。

        策略:
            1. 尝试整体解析
            2. 尝试 Markdown 代码块提取 (```json / ```)
            3. 首尾大括号/中括号裁剪
            4. 正则查找第一个 [ ... ] 或 { ... }
            5. 最后尝试逐行拼接修复
        """
        text = text.strip()

        # 1. 直接解析
        try:
            result = json.loads(text)
            if isinstance(result, list):
                return result
            # 如果结果是 dict，可能是 {"plan": [...]} 格式
            if isinstance(result, dict):
                for val in result.values():
                    if isinstance(val, list):
                        return val
        except json.JSONDecodeError:
            pass

        # 2. Markdown 代码块提取
        for marker in ["```json\n", "```\n", "```json", "```"]:
            if marker in text:
                _, after = text.split(marker, 1)
                if marker.endswith("\n"):
                    after = text.split(marker, 1)[1]
                else:
                    after = text.split(marker, 1)[1]
                text = after.split("```")[0] if "```" in after else after
                text = text.strip()
                try:
                    result = json.loads(text)
                    if isinstance(result, list):
                        return result
                except json.JSONDecodeError:
                    pass

        # 3. 找第一个 [ 和最后一个 ]
        start = text.find("[")
        end = text.rfind("]")
        if start >= 0 and end > start:
            candidate = text[start:end + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass

        # 4. 找第一个 { 和最后一个 }
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            candidate = text[start:end + 1]
            try:
                result = json.loads(candidate)
                if isinstance(result, dict):
                    for val in result.values():
                        if isinstance(val, list):
                            return val
                return [result]
            except json.JSONDecodeError:
                pass

        # 5. 最后尝试：逐行拼接，过滤非 JSON 行
        lines = text.splitlines()
        json_lines = []
        in_json = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("[") or stripped.startswith("{"):
                in_json = True
            if in_json:
                json_lines.append(stripped)
            if stripped.endswith("]") or stripped.endswith("}"):
                break
        if json_lines:
            try:
                return json.loads(" ".join(json_lines))
            except json.JSONDecodeError:
                pass

        # 全部失败
        raise json.JSONDecodeError(
            f"无法从响应中提取 JSON: {_truncate(text, 200)}",
            text, 0,
        )

    # ── 工具 ────────────────────────────────────

    @staticmethod
    def _normalize_chunks(chunks: List[Union[Dict, ChunkForLLM]]) -> List[ChunkForLLM]:
        result: List[ChunkForLLM] = []
        for c in chunks:
            if isinstance(c, ChunkForLLM):
                result.append(c)
            elif isinstance(c, dict):
                result.append(ChunkForLLM(
                    content=c.get("content", ""),
                    filename=c.get("filename", ""),
                    course=c.get("course", ""),
                    score=c.get("score", 0.0),
                ))
        return result


def _truncate(text: str, max_len: int) -> str:
    return text[:max_len] + "..." if len(text) > max_len else text
