from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_copilot_cli_repair_is_fork_safe_and_owner_gated():
    text = (
        ROOT / ".github" / "workflows" / "copilot-cli-ci-repair.yml"
    ).read_text(encoding="utf-8")
    assert 'workflows: ["CI"]' in text
    assert "github.event.workflow_run.head_repository.full_name == github.repository" in text
    assert "github.event.workflow_run.actor.login == github.repository_owner" in text
    assert "github.event.workflow_run.event == 'pull_request'" in text
    assert "p[\"state\"] != \"open\"" in text
    assert "p[\"base\"][\"ref\"] != \"master\"" in text
    assert "pull_request_target" not in text


def test_copilot_cli_repair_is_bounded():
    text = (
        ROOT / ".github" / "workflows" / "copilot-cli-ci-repair.yml"
    ).read_text(encoding="utf-8")
    assert "--max-ai-credits=60" in text
    assert "--max-autopilot-continues=2" in text
    assert "--available-tools='read,write,shell(git:*),shell(pytest)'" in text
    assert "--deny-tool='shell(git push)'" in text
    assert 'git commit -m "FIX: autonomous CI repair"' in text
    assert "python -m pytest -q" in text
    assert "workflow_dispatch:" in text


def test_copilot_cli_repair_does_not_delegate_scientific_decisions():
    text = (
        ROOT / ".github" / "workflows" / "copilot-cli-ci-repair.yml"
    ).read_text(encoding="utf-8")
    for marker in (
        "research/evidence/*",
        "research/preregistrations/*",
        "research/authorizations/*",
        "research gates",
        "holdout logic",
        "strategy parameters",
        "promotion rules",
        "live-trading controls",
    ):
        assert marker in text
