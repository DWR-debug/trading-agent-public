# F2 SEC Cloud Source Feasibility — 2026-09-28

Status: DATA_ACCESS_CONSTRAINT / NO PERFORMANCE AUTHORIZATION

A dedicated cloud probe tested the exact official SEC submissions and XBRL Company Facts endpoints used by the F1/F2 feasibility layer.

On 2026-09-28 the cloud runner returned HTTP 403 for both endpoints. The probe records these responses as DATA_INSUFFICIENT rather than turning an access problem into a scientific performance result.

The project's self-hosted Windows F1 feasibility run completed the corresponding source/PIT path successfully. SEC source access is therefore environment-dependent: the self-hosted PC is the current authoritative execution environment for SEC-based feasibility, while cloud remains useful for structural and non-SEC cross-checks.

This finding does not authorize F2 performance evaluation and does not establish profitability.
