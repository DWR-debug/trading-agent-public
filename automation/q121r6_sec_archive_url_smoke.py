from __future__ import annotations

import urllib.request

from automation.q121r6_sec_acceptance_time_compiler import archive_header_url

FILENAME = "edgar/data/1007587/000110465924093411/0001104659-24-093411-index.htm"
EXPECTED_PREFIX = "https://www.sec.gov/Archives/edgar/data/1007587/000110465924093411/"
EXPECTED_URL = EXPECTED_PREFIX + "0001104659-24-093411-index-headers.html"

def main() -> None:
    url = archive_header_url(FILENAME)
    assert url == EXPECTED_URL, (url, EXPECTED_URL)
    req = urllib.request.Request(url, headers={"User-Agent": "trading-agent-public/Q121R6-smoke/1"})
    with urllib.request.urlopen(req, timeout=30) as response:
        status = int(getattr(response, "status", 200))
    assert status == 200, status
    print("Q121R6_WINDOWS_URL_SMOKE_OK")
    print("Q121R6_SMOKE_URL=" + url)
    print("Q121R6_SMOKE_HTTP_STATUS=" + str(status))

if __name__ == "__main__":
    main()