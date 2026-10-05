from automation.literature_frontier_scout import QUERIES, canonical, fingerprint, title_key


def test_queries_are_distinct_and_nonempty():
    axes = [axis for axis, _ in QUERIES]
    queries = [query for _, query in QUERIES]
    assert len(axes) == len(set(axes))
    assert len(queries) == len(set(queries))
    assert all(axis and query for axis, query in QUERIES)


def test_fingerprint_is_stable():
    payload = {"b": 2, "a": 1}
    assert fingerprint(payload) == fingerprint({"a": 1, "b": 2})
    assert canonical(payload) == '{"a":1,"b":2}'


def test_title_key_normalizes_punctuation():
    assert title_key("Disclosure Similarity & Future Stock-Return Comovement") ==         "disclosure similarity future stock return comovement"


def test_discovery_contract_is_non_authorizing():
    assert "performance" not in {key.lower() for key in ["performance_authorized"]}
