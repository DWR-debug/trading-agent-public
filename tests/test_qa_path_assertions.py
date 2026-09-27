from pathlib import Path


def test_qa_path_assertions_use_single_windows_backslashes():
    text = Path("tests/test_self_hosted_research_worker.py").read_text(encoding="utf-8")
    assert "r'set \"WORK=%RUNNER_TEMP%\\trading-agent-continuous-%RUN_KEY%-%LANE%\"'" in text
    assert "r'set \"PROV_ROOT=%GITHUB_WORKSPACE%\\research\\runs\\self_hosted\"'" in text
