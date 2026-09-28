from automation.self_hosted_capacity import configured_secondary_roots

def test_unconfigured_sibling_is_not_eligible(tmp_path, monkeypatch):
    home = tmp_path
    monkeypatch.setenv("USERPROFILE", str(home))
    primary = home / "actions-runner"
    primary.mkdir()
    sibling = home / "actions-runner-2"
    sibling.mkdir()
    assert configured_secondary_roots(primary) == []
