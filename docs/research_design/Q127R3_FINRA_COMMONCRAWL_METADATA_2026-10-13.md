# Q127-R3 — Common Crawl metadata for FINRA daily history

**Scope:** alternative historical archive index; metadata only  
**Upstream frozen sample:** [Q127-R1 Run #38455702686](https://github.com/DWR-debug/trading-agent-public/actions/runs/38455702686)  
**Upstream fingerprint:** `2cbe22c49d885f527ac523ed74ab1e13a843c23999916c674282de6977e9c33c`

Q127-R2 queried Internet Archive CDX and two captured FINRA listing pages but did not recover an archived target-file payload/capture; two queries were incomplete due transport errors. This follow-up uses the separate Common Crawl monthly URL index. It fetches the collection index once, then at most one exact-URL query per one of the four preregistered FINRA daily text files. No FINRA target file or WARC record is downloaded.

The selected crawl's advertised date interval must intersect the fixed interval from the target report date through 30 days after it. This includes a crawl that began before the target date but continued across it, which could still have captured the file afterward. The actual per-URL capture timestamp is then checked independently; only captures from 0 to 45 days after the target report date count as near-window observations. A Common Crawl timestamp is the time the crawler observed the URL, not FINRA's first publication time. A positive observation can bound availability by that crawl timestamp; absence does not prove the file was never published. The indexed SHA-1 digest is retained as metadata and is not directly compared with the Q127-R1 SHA-256 receipt.

**Success meaning:** the bounded source/index queries completed and the returned metadata met the frozen schema. This does not prove exact first-publication time, revision lineage, or same-day PIT safety.

Source: [Common Crawl CDXJ index](https://www.commoncrawl.org/cdxj-index); [Common Crawl URL index](https://commoncrawl.org/url-index).
