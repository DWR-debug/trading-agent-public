from datetime import date
import pytest

from automation.information_alpha_redundancy_long_window import CHUNK_WINDOWS, DEFAULT_END, DEFAULT_START, MIN_EVENT_WINDOWS, MIN_TOTAL_OBSERVATIONS, aggregate_q014_chunks

def test_q014_window_is_exactly_365_calendar_days():
    assert (DEFAULT_END - DEFAULT_START).days == 364

def test_q014_chunk_windows_cover_exact_preregistered_window_without_overlap():
    assert CHUNK_WINDOWS[0][1] == DEFAULT_START
    assert CHUNK_WINDOWS[-1][2] == DEFAULT_END
    for left, right in zip(CHUNK_WINDOWS, CHUNK_WINDOWS[1:]):
        assert left[2].toordinal() + 1 == right[1].toordinal()
    assert sum((end-start).days+1 for _,start,end in CHUNK_WINDOWS) == 365

def test_q014_fixed_data_contract_thresholds():
    assert MIN_TOTAL_OBSERVATIONS == 80
    assert MIN_EVENT_WINDOWS == 40

def test_q014_rejects_non_365_day_window_without_network():
    from automation.information_alpha_redundancy_long_window import run_q014
    with pytest.raises(ValueError):
        run_q014(date(2025,9,26),date(2026,9,24),output_dir="/tmp/q014-test")

def test_q014_aggregate_requires_all_chunks(tmp_path):
    with pytest.raises(FileNotFoundError):
        aggregate_q014_chunks(chunk_dir=tmp_path,output_dir=tmp_path/"out")
