from automation import q221_transaction_parent_uei_probe as probe


def test_seven_transaction_keys_are_unique_and_frozen():
    assert len(probe.SAMPLES)==7
    assert len({x[0] for x in probe.SAMPLES})==7
    assert len({x[1] for x in probe.SAMPLES})==7
    assert probe.MAX_ROWS==10000 and probe.MAX_ZIP==20_000_000
    assert probe.FROZEN["APPLY_HISTORICAL_MAPPING"]=="false"


def test_download_query_uses_exact_award_ids_and_action_dates():
    filters={"award_ids":[f'"{s[1]}"' for s in probe.SAMPLES],"time_period":[{"start_date":s[3],"end_date":s[3],"date_type":"action_date"} for s in probe.SAMPLES]}
    assert len(filters["award_ids"])==7 and len(filters["time_period"])==7
    assert all(x["start_date"]==x["end_date"] for x in filters["time_period"])
