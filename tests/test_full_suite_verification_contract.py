from pathlib import Path


def test_full_suite_verification_propagates_pytest_failure_exit_code():
    workflow = Path(".github/workflows/full-suite-verification.yml").read_text(encoding="utf-8")
    pytest_step = workflow.split("name: Run full pytest suite", 1)[1].split("name: Diagnose pytest result", 1)[0]

    assert "set +e" in pytest_step
    assert "set -o pipefail" in pytest_step
    assert "python -m pytest -q 2>&1 | tee \"$RUNNER_TEMP/pytest.log\"" in pytest_step
    assert "pytest_exit_code=${PIPESTATUS[0]}" in pytest_step
    assert 'echo "exit_code=$pytest_exit_code" >> "$GITHUB_OUTPUT"' in pytest_step
    assert "if: steps.pytest.outputs.exit_code != '0'" in workflow
    assert "name: Fail job on pytest failure" in workflow
