"""精简后的 orchestrator 测试。"""
import pytest
from unittest.mock import MagicMock, patch
from backend.agent.orchestrator import SuperTutorAgent


@pytest.fixture
def agent():
    mock_vs = MagicMock()
    mock_vs.get_source_files.return_value = {}
    with (
        patch("backend.agent.orchestrator.VectorStore", return_value=mock_vs),
        patch("backend.agent.orchestrator.CitationLLM"),
        patch("backend.agent.orchestrator.load_dotenv"),
    ):
        a = SuperTutorAgent()
        a.vector_store = mock_vs
        yield a


class TestIngest:
    def test_normal_pdf(self, agent, tmp_path):
        pdf = tmp_path / "test.pdf"
        pdf.write_text("dummy")
        with patch.object(agent.parser, "parse") as mp:
            mp.return_value = MagicMock(text="aaa", filename="test.pdf", scanned=False, doc_type="textbook")
            r = agent.ingest_document(str(pdf))
            assert r["ok"]

    def test_scanned_rejected(self, agent, tmp_path):
        pdf = tmp_path / "scan.pdf"
        pdf.write_text("x")
        with patch.object(agent.parser, "parse") as mp:
            mp.return_value = MagicMock(text="", filename="scan.pdf", scanned=True)
            r = agent.ingest_document(str(pdf))
            assert r["ok"] is False and r["reason"] == "scanned_pdf"

    def test_duplicate(self, agent, tmp_path):
        agent._sources["dup.pdf"] = {}
        pdf = tmp_path / "dup.pdf"
        pdf.write_text("x")
        r = agent.ingest_document(str(pdf))
        assert r["ok"] is False and r["reason"] == "duplicate"
