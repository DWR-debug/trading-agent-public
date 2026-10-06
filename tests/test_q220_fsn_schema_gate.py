from automation import q220_fsn_schema_gate as gate

def test_q220_schema_gate(tmp_path, monkeypatch):
    import io, zipfile
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr("sub.tsv", "adsh\tname\nA\tX\n")
        z.writestr("tag.tsv", "tag\tversion\nCash\tstd\n")
        z.writestr("dim.tsv", "adsh\tdim\nA\tD\n")
        z.writestr("num.tsv", "adsh\ttag\nA\tCash\n")
        z.writestr("txt.tsv", "adsh\ttag\nA\tNote\n")
        z.writestr("pre.tsv", "adsh\ttag\nA\tCash\n")
    monkeypatch.setattr(gate, "fetch", lambda url: b.getvalue())
    r = gate.run(tmp_path / "r.json")
    assert r["schema_minimum_pass"] is True
    assert r["scientific_evidence"] is False