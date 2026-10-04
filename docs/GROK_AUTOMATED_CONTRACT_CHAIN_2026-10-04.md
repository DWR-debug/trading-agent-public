# Grok contract chain — 2026-10-04

The Grok workflow is now designed as a four-stage bounded contract chain. The operator only needs to start Contract 01 once. Each contract contains the exact URL of the next contract, and Grok is instructed to continue within the same conversation.

## Bootstrap

Send this once in a free Grok conversation:

Open and execute this contract:
https://raw.githubusercontent.com/DWR-debug/trading-agent-public/master/research/contracts/grok/01_adversarial_q194_q201.md

Follow each NEXT_CONTRACT_URL automatically in the same conversation until the chain reaches Contract 04. Do not ask me for another prompt unless a contract explicitly terminates with a blocking condition. Do not paste secrets.

## Chain

01 — Q194–Q201 adversarial review
02 — deterministic gate matrix and action handoff
03 — current receipt/state recheck
04 — independent challenge and terminal handoff

The chain is bounded. It does not authorize research performance, select holdouts/assets/parameters/horizons, promote candidates, or execute live trading.

## Important limitation

This automates contract retrieval and sequential reasoning inside the Grok conversation. It does not make Grok write results back into the repository. A result still becomes operational project state only after the Trading-Agent Orchestrator receives and independently verifies it.

Current xAI documentation describes Grok as free to start on the web/apps, while xAI's developer API is usage-priced/prepaid. Therefore the chain intentionally uses the consumer Grok route and does not require a paid xAI API key under the project's $0 paid-resource policy.
