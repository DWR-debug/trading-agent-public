"""Bounded Q121-R6 SEC archive URL smoke checks.

No network access and no scientific evidence are produced. The checks lock the
repository-path CIK, normalized accession directory and dashed index-header
filename against known SEC archive layouts.
"""
from __future__ import annotations

from automation.q121r6_sec_acceptance_time_compiler import archive_header_url


CONTROLS = (
    (
        "edgar/data/1590750/000110465924100769/"
        "0001104659-24-100769-index.htm",
        "https://www.sec.gov/Archives/edgar/data/1590750/000110465924100769/"
        "0001104659-24-100769-index-headers.html",
    ),
    (
        "edgar/data/1002242/000110465924079110/"
        "0001104659-24-079110-index.htm",
        "https://www.sec.gov/Archives/edgar/data/1002242/000110465924079110/"
        "0001104659-24-079110-index-headers.html",
    ),
)


def main() -> int:
    for filename, expected in CONTROLS:
        actual = archive_header_url(filename)
        if actual != expected:
            raise SystemExit(
                f"Q121R6_ARCHIVE_URL_SMOKE_FAILED:{filename}:{actual}:{expected}"
            )
        if "/data/1104659/" in actual:
            raise SystemExit(f"Q121R6_ARCHIVE_URL_SMOKE_WRONG_CIK_ROOT:{actual}")
        print(f"Q121R6_ARCHIVE_URL_SMOKE_OK {filename} -> {actual}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())