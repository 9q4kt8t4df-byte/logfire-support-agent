import pytest
from pathlib import Path
from tools.knowledge_tool import KnowledgeTool


@pytest.fixture
def tool(tmp_path):
    # Create test knowledge files
    (tmp_path / "issue_alpha.md").write_text(
        "# Alpha Error\n\nThe alpha service throws 503 when connector timeout happens upstream."
    )
    (tmp_path / "issue_beta.md").write_text(
        "# Beta Race Condition\n\nConcurrent writes to the state table cause duplicate key errors."
    )
    return KnowledgeTool(knowledge_dir=str(tmp_path))


def test_search_returns_matches(tool):
    results = tool.search_known_issues("connector timeout")
    assert len(results) >= 1
    assert any("alpha" in r.lower() or "connector" in r.lower() for r in results)


def test_search_returns_empty_for_unknown(tool):
    results = tool.search_known_issues("xyzzy_nonexistent_pattern_99")
    assert results == []


def test_search_is_case_insensitive(tool):
    results_lower = tool.search_known_issues("race condition")
    results_upper = tool.search_known_issues("RACE CONDITION")
    assert len(results_lower) == len(results_upper)


def test_get_runbook_returns_content(tool):
    content = tool.get_runbook("alpha")
    assert "503" in content or "alpha" in content.lower()


def test_get_runbook_returns_not_found_message(tool):
    content = tool.get_runbook("nonexistent_runbook_xyz")
    assert "not found" in content.lower()
