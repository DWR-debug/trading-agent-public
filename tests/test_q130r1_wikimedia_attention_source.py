from automation.q130r1_wikimedia_attention_source import (
    END,
    START,
    article_url,
    compile_items,
    parse_items,
)

def test_article_url_is_frozen():
    url = article_url("S&P Global")
    assert url.endswith("/S%26P_Global/daily/20250920/20250924")
    assert START == "20250920"
    assert END == "20250924"

def test_parse_and_compile_daily_items():
    body = b'{"items":[{"timestamp":"20250921","views":18},{"timestamp":"20250920","views":12}]}'
    items = parse_items(body)
    assert compile_items(items) == {"20250920": 12, "20250921": 18}

def test_parse_rejects_missing_items():
    import pytest
    with pytest.raises(RuntimeError, match="WIKIMEDIA_ITEMS_MISSING"):
        parse_items(b'{"foo": []}')

def test_parse_rejects_invalid_views():
    import pytest
    with pytest.raises(RuntimeError, match="WIKIMEDIA_VIEWS_INVALID"):
        parse_items(b'{"items":[{"timestamp":"20250920","views":-1}]}')

def test_compile_is_order_invariant():
    a = [{"timestamp":"20250920","views":12},{"timestamp":"20250921","views":18}]
    b = list(reversed(a))
    assert compile_items(a) == compile_items(b)

def test_scientific_boundary_is_not_embedded_in_source_url():
    assert "performance" not in article_url("Nasdaq").lower()
