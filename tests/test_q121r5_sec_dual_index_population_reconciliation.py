from collections import Counter

from automation.q121r5_sec_dual_index_population_reconciliation import canonical_keys, counter_fingerprint


def test_canonical_keys_preserve_duplicates():
    rows = [
        {"cik":"1","form":"SC 13G","filed_date":"2024-02-13","filename":"x/0000000001-24-000001-index.htm"},
        {"cik":"1","form":"SC 13G","filed_date":"2024-02-13","filename":"x/0000000001-24-000001-index.htm"},
    ]
    c = canonical_keys(rows, lambda x: x.rsplit("/",1)[-1].removesuffix("-index.htm"))
    assert c[("1","SC 13G","2024-02-13","0000000001-24-000001")] == 2


def test_counter_fingerprint_is_order_independent():
    a = Counter({("1","SC 13G","2024-02-13","A"): 2, ("2","SC 13G","2024-02-14","B"): 1})
    b = Counter({("2","SC 13G","2024-02-14","B"): 1, ("1","SC 13G","2024-02-13","A"): 2})
    assert counter_fingerprint(a) == counter_fingerprint(b)
