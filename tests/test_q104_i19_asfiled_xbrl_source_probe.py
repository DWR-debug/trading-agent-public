from automation.q104_i19_asfiled_xbrl_source_probe import CONCEPTS, FORMS, load_frozen_ciks


def test_i19_source_probe_uses_exact_frozen_universe_and_concepts():
    ciks = load_frozen_ciks()
    assert sorted(ciks) == ["AMP","DVN","EMN","NDAQ","RJF","SPGI","VLO","WMB"]
    assert FORMS == {"10-K","10-Q"}
    assert CONCEPTS == {
        "NetIncomeLoss",
        "NetCashProvidedByUsedInOperatingActivities",
        "Assets",
    }


def test_i19_source_probe_is_non_authorizing():
    from pathlib import Path
    source = Path("automation/q104_i19_asfiled_xbrl_source_probe.py").read_text(encoding="utf-8")
    assert '"performance_authorized": False' in source
    assert '"holdout_selection_allowed": False' in source
    assert '"live_execution_allowed": False' in source
