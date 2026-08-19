# Data manifest

This directory records exactly what was pulled from ClickHouse, when, and from where, so
Part 1's results can be traced back to their source. See `project-scope.md` for why each
of these choices was made; this file just records what happened.

## Source

ethpandaops Xatu ClickHouse cluster, `https://clickhouse.xatu.ethpandaops.io`, database
`default`, filtered to `meta_network_name = 'mainnet'`. Credentials are supplied via
`CLICKHOUSE_USERNAME` / `CLICKHOUSE_PASSWORD` or a local `secrets.json` (see repo root
`.gitignore`) — see `src/apx/config.py`.

## Frozen Part 1 range

`block_range.json` records the frozen 1,000,000-block range (`24783045..25783044`) and the
completeness checks run against it before freezing, per the sampling rule in
`project-scope.md`. That check queried `canonical_execution_block` for gaps, and
`canonical_execution_transaction` / `canonical_execution_storage_diffs` for transaction-index
ordering consistency and tip health, live on 2026-08-18.

## Queries

The exact SQL run for every extraction is in `queries/*.sql`, parameterized on
`{start_block}` / `{end_block}` and executed via `src/apx/extraction.py`. Every query
aggregates server-side (row counts, or `argMin`/`argMax`-reduced net mutations ordered by
`internal_index` / `(transaction_index, internal_index)`) so the client never downloads raw
event-level diff rows, only already-deduplicated keys, matching the data contract in
`project-scope.md`.

## Pilot extraction

A 10,000-block pilot (`24783045..24793044`, the first 1% of the frozen range) was run in
full on 2026-08-18 and cached at `data/pilot_10k/` (gitignored; regenerate with the command
below). It is the working dataset behind Part 1's current results — the full 1,000,000-block
range was not pulled in this pass; see the top-level README for why and how to run it.

| file | rows | sha256 |
|---|---|---|
| storage_reads_agg.parquet | 25,263,200 | c986e57596c029bcde45b62a4593cb68b79a760556f919498a5d8f2a18705bf5 |
| storage_tx_mutations.parquet | 8,929,303 | eae6b9235b2895d06b02f2d1260bd8695ab216d03357abb5bec86a232e2764b5 |
| storage_block_mutations.parquet | 8,016,205 | a0ae542ae9ae1c2668f15a172dbc210a5280513032a97a8cc16c3f2e4d0c46e6 |
| balance_reads_agg.parquet | 15,578,558 | 1ef66a37973245d875c58c2db20c3922a679bd8ad213c6a3ba551f36f425f0d7 |
| nonce_reads_agg.parquet | 14,588,880 | 588f6c8f232b695bf0752c2c14488a3225858ca5aa13e562050d16e130fc8e3c |
| balance_block_mutations.parquet | 5,100,942 | cee9a850a9d7576875c5e6a09aa845f69ddcbed1da0160f5ebd1497e6beb697f |
| nonce_block_mutations.parquet | 3,072,058 | 00a576be3abf5b7670abc18e8ae03b36f8b681e71e485fdc27db10a91dc2f09f |

Reproduce with:

```bash
python -c "
from pathlib import Path
from apx.config import load_config
from apx.extraction import extract_all

cfg = load_config()
extract_all(cfg, 24783045, 24793044, Path('data/pilot_10k'))
"
```

## Table schemas and coverage

Verified live against the source cluster on 2026-08-18: `canonical_execution_block`,
`canonical_execution_transaction`, `canonical_execution_storage_reads`,
`canonical_execution_storage_diffs`, `canonical_execution_balance_reads`,
`canonical_execution_balance_diffs`, `canonical_execution_nonce_reads`,
`canonical_execution_nonce_diffs` all cover mainnet blocks through `25783044` with no gaps
in the frozen range. Full-history row counts per table are in `block_range.json`.
