from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "temporal-identity-state-spine-waves.yml"


def test_windows_spine_result_is_staged_to_workspace_before_artifact_upload():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    stage_marker = "- name: Stage deterministic result for artifact upload"
    upload_marker = "name: spine-windows-${{ matrix.wave }}-${{ github.run_id }}"

    assert workflow.count(stage_marker) == 1
    stage_start = workflow.index(stage_marker)
    upload_start = workflow.index(upload_marker, stage_start)
    staging = workflow[stage_start:upload_start]

    assert stage_start < upload_start
    assert "        if: always()\n        shell: cmd" in staging
    assert r'SOURCE=%REPO_SRC%\research\runs\spine\${{ matrix.wave }}\%GITHUB_RUN_ID%\spine.json' in staging
    assert r'DEST=%GITHUB_WORKSPACE%\research\runs\spine\${{ matrix.wave }}\%GITHUB_RUN_ID%' in staging
    assert 'if not exist "%SOURCE%"' in staging
    assert 'copy /y "%SOURCE%" "%DEST%\\spine.json" >nul || exit /b 1' in staging
    assert "path: research/runs/spine/${{ matrix.wave }}/${{ github.run_id }}/" in workflow
