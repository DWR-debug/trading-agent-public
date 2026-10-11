from __future__ import annotations

import hashlib

from automation.q220_textblock_mismatch_diagnostic import (
    first_difference,
    independent_texts,
    primary_texts,
    state_differences,
)
from automation.q220_historical_representation_pit import textblock_states
from automation.q220_independent_pit_reproduction import parse_textblock_states


def test_primary_and_independent_visible_text_agree_on_nested_and_adjacent_facts():
    document = """
    <html xmlns:ix="http://www.xbrl.org/2013/inlineXBRL">
      <ix:nonNumeric name="custom:OuterTextBlock" contextRef="C1" id="outer">
        Outer before <ix:nonNumeric name="custom:InnerTextBlock" contextRef="C2" id="inner">Inner disclosure</ix:nonNumeric> outer after
      </ix:nonNumeric>
      <ix:nonNumeric name="custom:EmptyTextBlock" contextRef="C3" id="empty" />
      <ix:nonNumeric name="custom:LastTextBlock" contextRef="C4" id="last">Last disclosure</ix:nonNumeric>
    </html>
    """
    primary = primary_texts(document)
    independent = independent_texts(document)

    assert primary == independent
    assert textblock_states(document) == parse_textblock_states(document)
    assert primary["custom:OuterTextBlock"][("C1", "outer")][0] == "Outer before Inner disclosure outer after"
    assert primary["custom:EmptyTextBlock"][("C3", "empty")][0] == ""


def test_first_difference_reports_exact_divergent_character_and_context():
    diff = first_difference("alpha  beta", "alpha beta")
    assert diff is not None
    assert diff["index"] == 6
    assert diff["left_codepoint"] == "U+0020"
    assert diff["right_codepoint"] == "U+0062"
    assert "alpha" in diff["primary_context"]
    assert "alpha" in diff["independent_context"]


def test_state_difference_counter_names_only_different_fields():
    compiler_states = {
        "custom:RiskTextBlock": [{
            "context_ref": "C1",
            "fact_id": "fact-1",
            "continued_chain_length": 1,
            "continued_chain_complete": True,
            "normalized_character_count": 20,
            "content_sha256": hashlib.sha256(b"alpha beta").hexdigest(),
        }]
    }
    independent_states = {
        "custom:RiskTextBlock": [{
            "context_ref": "C1",
            "fact_id": "fact-1",
            "continued_chain_length": 1,
            "continued_chain_complete": True,
            "normalized_character_count": 21,
            "content_sha256": hashlib.sha256(b"alpha  beta").hexdigest(),
        }]
    }
    assert state_differences(compiler_states, independent_states) == {
        "content_sha256": 1,
        "normalized_character_count": 1,
    }
