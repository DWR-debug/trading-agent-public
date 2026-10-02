from automation.s10_candidate_redteam import review_payload, review_candidates


def test_redteam_payload_is_design_contract_only():
    payload = review_payload({
        "id": "X",
        "name": "Candidate",
        "hypothesis": "x",
        "construction": "y",
        "sources": ["source"],
        "next_gate": "source/PIT feasibility",
    })
    text = payload["state"]["evidence"]
    assert "Candidate" in text
    assert "performance" not in text.lower()
    assert "holdout" not in text.lower()


def test_redteam_parses_typed_responses(monkeypatch):
    def fake_request(url, payload, timeout):
        return {
            "answers": {
                "verdict": {
                    "choice": "INSUFFICIENT",
                    "probabilities": {
                        "SUPPORTED": 0.1,
                        "REFUTED": 0.1,
                        "INSUFFICIENT": 0.8,
                    },
                }
            }
        }

    monkeypatch.setattr("automation.s10_candidate_redteam._request", fake_request)
    rows = review_candidates(
        "http://127.0.0.1:8765",
        [{"id": "X", "family": "test"}],
        10,
    )
    assert rows[0]["predicted_contract_status"] == "INSUFFICIENT"
    assert rows[0]["error"] is None
