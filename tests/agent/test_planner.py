"""
单元测试 — StudyPlanner._extract_json
"""
import json
import pytest
from backend.agent.planner import StudyPlanner


p = StudyPlanner.__new__(StudyPlanner)
extract = p._extract_json


class TestExtractJson:
    def test_clean_json(self):
        assert extract('[{"day": 1, "task": "a"}]') == [{"day": 1, "task": "a"}]

    def test_markdown_code_block(self):
        text = "```json\n[{\"day\": 1, \"task\": \"a\"}]\n```"
        assert extract(text) == [{"day": 1, "task": "a"}]

    def test_extra_text_before_json(self):
        text = "以下是你的计划：\n[{\"day\": 1, \"task\": \"a\"}]\n祝学习顺利！"
        assert extract(text) == [{"day": 1, "task": "a"}]

    def test_dict_wrapper(self):
        text = "{\"plan\": [{\"day\": 1, \"task\": \"a\"}]}"
        result = extract(text)
        assert isinstance(result, list)
        assert len(result) == 1

    def test_empty_list(self):
        assert extract("[]") == []

    def test_single_object(self):
        text = "{\"day\": 1, \"task\": \"a\"}"
        result = extract(text)
        assert isinstance(result, list)
        assert len(result) >= 1
