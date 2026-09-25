"""Point-in-time parser for GDELT 2.0 Event export records."""
from __future__ import annotations
import csv
import io
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError
from urllib.request import Request, urlopen

GDELT_EVENT_FIELD_COUNT = 58
DATEADDED_INDEX = 56
SOURCEURL_INDEX = 57

class GDELTEventError(ValueError):
    """Raised for malformed GDELT event records."""


class GDELTDataUnavailableError(RuntimeError):
    """Raised when a requested historical GDELT daily export is unavailable."""

    def __init__(self, *, day: str, url: str, status_code: int):
        self.day = day
        self.url = url
        self.status_code = status_code
        super().__init__(
            f"GDELT daily export unavailable for {day}: HTTP {status_code} ({url})"
        )

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
    if len(value) == 8:
        return datetime.strptime(value, "%Y%m%d").replace(tzinfo=timezone.utc)
    if len(value) == 14:
        return datetime.strptime(value, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
    raise GDELTEventError(f"Unsupported DATEADDED format: {value!r}")

def _schema_indexes(field_count: int) -> tuple[int, int, int]:
    if field_count >= 61:
        return 61, 59, 60
    if field_count == 58:
        return 58, 56, 57
    raise GDELTEventError(
        f"Unsupported GDELT Event field count: {field_count}; expected 58 or 61."
    )

def parse_event_row(row: Iterable[str]) -> GDELTEvent:
    values = list(row)
    _, date_index, source_index = _schema_indexes(len(values))
    return GDELTEvent(
        event_id=_int(values, 0),
        date_added=_parse_timestamp(_text(values, date_index)),
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
        source_url=_text(values, source_index),
    )

def parse_event_tsv(
    text: str,
    *,
    strict: bool = True,
    stats: dict[str, int] | None = None,
) -> Iterable[GDELTEvent]:
    for row in csv.reader(io.StringIO(text), delimiter="\t"):
        if not row or not any(cell.strip() for cell in row):
            continue
        if stats is not None:
            stats["rows_seen"] = stats.get("rows_seen", 0) + 1
        try:
            yield parse_event_row(row)
        except (ValueError, GDELTEventError):
            if strict:
                raise
            if stats is not None:
                stats["rows_skipped"] = stats.get("rows_skipped", 0) + 1

def parse_event_zip(
    path: str | Path,
    *,
    strict: bool = True,
    stats: dict[str, int] | None = None,
) -> Iterable[GDELTEvent]:
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if not (name.endswith(".export.CSV") or name.endswith(".csv")):
                continue
            with archive.open(name) as raw:
                reader = csv.reader(
                    io.TextIOWrapper(raw, encoding="utf-8", errors="replace"),
                    delimiter="\t",
                )
                for row in reader:
                    if not row or not any(cell.strip() for cell in row):
                        continue
                    if stats is not None:
                        stats["rows_seen"] = stats.get("rows_seen", 0) + 1
                    try:
                        yield parse_event_row(row)
                    except (ValueError, GDELTEventError):
                        if strict:
                            raise
                        if stats is not None:
                            stats["rows_skipped"] = stats.get("rows_skipped", 0) + 1

def daily_export_url(day: datetime) -> str:
    return f"https://data.gdeltproject.org/events/{day.astimezone(timezone.utc):%Y%m%d}.export.CSV.zip"

def download_daily_export(day: datetime, destination: str | Path) -> Path:
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    url = daily_export_url(day)
    request = Request(url, headers={"User-Agent": "trading-agent-research/1.0"})
    try:
        with urlopen(request, timeout=60) as response, destination.open("wb") as target:
            target.write(response.read())
    except HTTPError as exc:
        if exc.code == 404:
            raise GDELTDataUnavailableError(
                day=day.astimezone(timezone.utc).date().isoformat(),
                url=url,
                status_code=exc.code,
            ) from exc
        raise
    return destination
