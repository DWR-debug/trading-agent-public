"""Point-in-time parser for GDELT 2.0 Event export records."""
from __future__ import annotations
import csv
import io
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.request import Request, urlopen

GDELT_EVENT_FIELD_COUNT = 58
DATEADDED_INDEX = 56
SOURCEURL_INDEX = 57

class GDELTEventError(ValueError):
    """Raised for malformed GDELT event records."""

@dataclass(frozen=True)
class GDELTEvent:
    event_id: int
    date_added: datetime
    event_code: str
    event_base_code: str
    event_root_code: str
    quad_class: int
    goldstein_scale: float
    num_mentions: int
    num_sources: int
    num_articles: int
    avg_tone: float
    actor1_country_code: str
    actor2_country_code: str
    actor_geo_country_code: str
    source_url: str

def _text(row: list[str], index: int) -> str:
    return row[index].strip() if index < len(row) else ""

def _int(row: list[str], index: int, *, default: int | None = None) -> int:
    value = _text(row, index)
    if not value:
        if default is None:
            raise GDELTEventError(f"Missing integer field at index {index}.")
        return default
    return int(value)

def _float(row: list[str], index: int, *, default: float | None = None) -> float:
    value = _text(row, index)
    if not value:
        if default is None:
            raise GDELTEventError(f"Missing float field at index {index}.")
        return default
    return float(value)

def _parse_timestamp(value: str) -> datetime:
    if not value:
        raise GDELTEventError("DATEADDED is empty.")
    return datetime.strptime(value, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)

def parse_event_row(row: Iterable[str]) -> GDELTEvent:
    values = list(row)
    if len(values) < GDELT_EVENT_FIELD_COUNT:
        raise GDELTEventError(f"Expected at least {GDELT_EVENT_FIELD_COUNT} fields, got {len(values)}.")
    return GDELTEvent(
        event_id=_int(values, 0),
        date_added=_parse_timestamp(_text(values, DATEADDED_INDEX)),
        event_code=_text(values, 26),
        event_base_code=_text(values, 27),
        event_root_code=_text(values, 28),
        quad_class=_int(values, 29),
        goldstein_scale=_float(values, 30),
        num_mentions=_int(values, 31, default=0),
        num_sources=_int(values, 32, default=0),
        num_articles=_int(values, 33, default=0),
        avg_tone=_float(values, 34, default=0.0),
        actor1_country_code=_text(values, 7),
        actor2_country_code=_text(values, 17),
        actor_geo_country_code=_text(values, 52),
        source_url=_text(values, SOURCEURL_INDEX),
    )

def parse_event_tsv(text: str) -> Iterable[GDELTEvent]:
    for row in csv.reader(io.StringIO(text), delimiter="\t"):
        if row and any(cell.strip() for cell in row):
            yield parse_event_row(row)

def parse_event_zip(path: str | Path) -> Iterable[GDELTEvent]:
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if name.endswith(".export.CSV") or name.endswith(".csv"):
                with archive.open(name) as raw:
                    reader = csv.reader(io.TextIOWrapper(raw, encoding="utf-8", errors="replace"), delimiter="\t")
                    for row in reader:
                        if row and any(cell.strip() for cell in row):
                            yield parse_event_row(row)

def daily_export_url(day: datetime) -> str:
    return f"https://data.gdeltproject.org/events/{day.astimezone(timezone.utc):%Y%m%d}.export.CSV.zip"

def download_daily_export(day: datetime, destination: str | Path) -> Path:
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = Request(daily_export_url(day), headers={"User-Agent": "trading-agent-research/1.0"})
    with urlopen(request, timeout=60) as response, destination.open("wb") as target:
        target.write(response.read())
    return destination
