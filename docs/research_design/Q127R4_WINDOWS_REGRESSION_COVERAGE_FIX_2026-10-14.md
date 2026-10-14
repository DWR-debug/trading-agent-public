# Q127-R4 — Windows regression coverage fix

**Date:** 2026-10-14
**Official source-probe run:** https://github.com/DWR-debug/trading-agent-public/actions/runs/38524386024
**Receipt fingerprint:** d46afc902510c6d63f8c5cb38a58b0a6e08a5573e0c539a16e7376ab4acd57ea

The Q127-R4 test file was listed as a path trigger for Windows Candidate Gate Regression Wave but was missing from the Q127 pack's pytest command. Thus, the source workflow and Ubuntu CI exercised its tests, while the Windows pack silently omitted them.

This fix adds the Q127-R4 test module to the fixed Q127 Windows command and adds a regression assertion that the command continues to include it. The four fixed dates and eight symbols remain unchanged; no data-file payload is downloaded and no PIT gate is cleared. The Q127-R4 source probe remains metadata-only and non-authorizing.
