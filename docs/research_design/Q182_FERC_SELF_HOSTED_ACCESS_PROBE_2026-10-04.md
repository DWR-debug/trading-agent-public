# Q182 FERC Self-Hosted Access Probe — 2026-10-04

Q182 is currently blocked only because the GitHub-hosted source probe receives
HTTP 403 from the FERC eLibrary pages. This bounded data-QA probe uses both
verified Windows self-hosted research lanes (`local_reproduction` and `data_qa`)
to distinguish a hosted-network block from a broader source-access block.

A PASS here would only establish operational source reachability from the
Windows runners. It would not establish historical completeness, PIT validity,
entity mapping, revision lineage, performance, or promotion.