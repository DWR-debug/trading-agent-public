from automation.q125_f1_sec_publication_clock import mutation_tests, match_rss_for_vintage


def test_mutation_contract():
    assert all(mutation_tests().values())


def test_vintage_matching_is_order_invariant():
    items = [
        {"title": "Metrics by Individual Security 2025 Q1", "link": "q1", "pubDate": "2025-04-01"},
        {"title": "Metrics by Individual Security 2025 Q2", "link": "q2", "pubDate": "2025-07-01"},
    ]
    assert match_rss_for_vintage(items, "2025 Q1") == match_rss_for_vintage(list(reversed(items)), "2025 Q1")


def test_future_vintage_does_not_match_historical_clock():
    items = [{"title": "Metrics by Individual Security 2025 Q1", "link": "q1", "pubDate": "2025-04-01"}]
    items.append({"title": "Metrics by Individual Security 2099 Q4", "link": "q4", "pubDate": "2099-10-01"})
    assert len(match_rss_for_vintage(items, "2025 Q1")) == 1
