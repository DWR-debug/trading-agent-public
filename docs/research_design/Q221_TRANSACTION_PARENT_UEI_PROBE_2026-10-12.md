# Q221 transaction-level parent UEI probe — preregistration

Seven exact transaction keys across 2019–2024 were selected from the frozen 348-row sample, each with a verified current-profile parent lead. Source receipt fingerprint: 9e738733d369bf4a954e74cd999c4ba462cf0f9a4fa44aa65c74c637cf3b11f4. Current parent map: run #38305074104, artifact q221-current-parent-identity-map-38305074104-1, fingerprint ae3a3263d5e7d2545dbdaed7ba7ff1cfe3d4cd00e0403352096dcce4d4797602.

The official USAspending advanced transaction download contract supports exact award IDs and action-date filters. Its download-column mapping exposes `recipient_parent_uei` mapped from transaction-level `ultimate_parent_uei` in FPDS/FABS records:
- https://github.com/fedspendingtransparency/usaspending-api/blob/master/usaspending_api/api_contracts/contracts/v2/download/transactions.md
- https://github.com/fedspendingtransparency/usaspending-api/blob/master/usaspending_api/download/v2/download_column_historical_lookups.py

The workflow first calls the documented count endpoint and refuses more than 10,000 rows, then downloads at most 20 MB and matches the seven frozen tuples exactly. This is a current transaction-table view, not an immutable first-public snapshot. A returned parent UEI is a lead, not proof of historical parent lineage or issuer identity. No mapping gate is cleared and no performance, ranking, tuning, promotion or live execution is enabled.
