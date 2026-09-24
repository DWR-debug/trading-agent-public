from data.gdelt_events import GDELT_EVENT_FIELD_COUNT, parse_event_row, parse_event_tsv

def row():
    values = [""] * GDELT_EVENT_FIELD_COUNT
    values[0], values[7], values[17] = "123", "USA", "RUS"
    values[26], values[27], values[28], values[29] = "190", "190", "19", "3"
    values[30], values[31], values[32], values[33], values[34] = "-3.5", "12", "4", "3", "-2.0"
    values[51], values[56], values[57] = "SY", "20260924123000", "https://example.com"
    return values

def test_point_in_time_parser():
    event = parse_event_row(row())
    assert event.event_id == 123
    assert event.date_added.isoformat() == "2026-09-24T12:30:00+00:00"
    assert event.event_root_code == "19"
    assert event.quad_class == 3

def test_tsv_parser():
    assert len(tuple(parse_event_tsv("\t".join(row()) + "\n"))) == 1
