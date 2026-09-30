from __future__ import annotations

from pathlib import Path


def test_c29r1_input_freeze_has_fixed_source_identity() -> None:
    source = Path("automation/c29r1_input_freeze.py").read_text(encoding="utf-8")
    assert 'TRIAL_ID = "T-2026-09-30-C29R1-INPUT-FREEZE"' in source
    assert 'COVERAGE_ARTIFACT_ID = 11111130029' in source
    assert 'COVERAGE_WORKFLOW_RUN_ID = 36741493347' in source
    assert 'SNAPSHOT_FINGERPRINT = "ca54223f855f3f11cff3868ff1287ec7a544e61036b35b6f0f3f29cab4a12e50"' in source
    assert 'COVERAGE_FINGERPRINT = "6b3acf5fb179bc93c6fac8eaaef59d71aa909326d5f171d9718a7cfbc71e22a6"' in source
    assert '"performance_evaluation": False' in source
    assert '"performance_authorized": False' in source


def test_c29r1_input_freeze_supports_flattened_artifact_layout() -> None:
    source = Path("automation/c29r1_input_freeze.py").read_text(encoding="utf-8")
    assert 'source_root / "c29r1_coverage" / COVERAGE_TRIAL_ID' in source
