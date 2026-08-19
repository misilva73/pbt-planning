# Access-pattern exploration: PBT account-header sizing

Empirical sizing of the PBT account-header storage window, per
[project-scope.md](project-scope.md). This is Part 1 only: storage-window locality and
stem replay, `S=0..253` with `C=0`. Code-chunk and joint allocation analysis (Parts 2-4)
are deferred.

## Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Credentials for the ethpandaops ClickHouse cluster come from environment variables
(`CLICKHOUSE_USERNAME`, `CLICKHOUSE_PASSWORD`) or a local `secrets.json` (see
`src/apx/config.py`); neither is committed. Copy `config/config.example.yaml` to
`config/config.local.yaml` if you want to override the default sampling range.

## Reproduce the report

```bash
python scripts/run_part1.py
```

This reads the cached 10,000-block pilot extraction at `data/pilot_10k/` (not committed;
see below to regenerate it) and writes `reports/part1_pilot/report.md` plus its figures.

### Regenerate the pilot extraction

```bash
python -c "
from pathlib import Path
from apx.config import load_config
from apx.extraction import extract_all
extract_all(load_config(), 24783045, 24793044, Path('data/pilot_10k'))
"
```

Takes a few minutes; see `manifest/README.md` for row counts and checksums.

### Run the full frozen 1,000,000-block range

The frozen Part 1 range is `24783045..25783044` (`manifest/block_range.json`). This is
**not** something to run in one sitting: the pilot above (1% of the range) already pulls
~25M read-event rows, and every table scales roughly linearly, so the full range is on the
order of billions of rows and many hours of ClickHouse + network time. Use the chunked,
resumable extractor instead of `extract_all`:

```bash
python -c "
from pathlib import Path
from apx.config import load_config
from apx.extraction import extract_all_chunked, merge_chunks
cfg = load_config()
extract_all_chunked(cfg, 24783045, 25783044, Path('data/full_1m_chunks'), chunk_size=10_000)
merge_chunks(Path('data/full_1m_chunks'), Path('data/full_1m'))
"
```

`extract_all_chunked` writes one parquet part per 10,000-block chunk and skips parts that
already exist, so a killed or interrupted run can be restarted with the same call.
`merge_chunks` collapses the parts into the single-file-per-query layout `run_part1.py`
expects once the extraction is complete (or you want to inspect it partway through).
Then run `python scripts/run_part1.py data/full_1m reports/part1_full`.

## Tests

```bash
pytest
```

49 tests, covering normalization, classification, key/stem derivation, the S-sweep replay
math, BASIC_DATA co-location, figure building, and report assembly — including an
end-to-end smoke test against the real pilot data.

## Package layout

- `src/apx/config.py`, `clickhouse.py`, `extraction.py` — configuration, ClickHouse
  client, and the pinned queries in `queries/*.sql`.
- `src/apx/normalize.py`, `keys.py`, `classify.py`, `replay.py`, `basic_data.py` — the
  analytical core: address/slot normalization, header stem/leaf key derivation, read
  classification, the S-sweep locality and leaf/stem replay math, and the observed
  BASIC_DATA co-location proxy.
- `src/apx/pipeline.py` — `build_results_table()` and `validation_summary()`, the single
  entry point tying the core together into one tidy results table.
- `src/apx/figures.py`, `report.py` — seaborn/matplotlib figures and the markdown report.
- `scripts/run_part1.py` — the reproduction entry point.
- `manifest/` — frozen block range, completeness checks, and pilot-extraction checksums.
- `queries/` — the exact SQL run against ClickHouse.

## Known limitations of this pass

Reported in full in `reports/part1_pilot/report.md`'s limitations section, plus:

1. Results are computed on a 10,000-block pilot (1% of the frozen 1,000,000-block range),
   not the full range — see "Run the full frozen 1,000,000-block range" above.
2. Temporal sensitivity (10 sub-range buckets) and idealized oracle ceilings (research
   question 5) were not computed in this pass.
3. Contract-category segmentation (Part 4) is out of scope for Part 1 by design.
