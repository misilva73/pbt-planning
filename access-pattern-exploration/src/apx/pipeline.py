"""Ties normalize/classify/replay/basic_data together into the Part 1 results contract.

`build_results_table` is the single entry point the report/plotting layer depends on. It
returns one tidy long-format DataFrame with exactly these columns:

- metric: "event_locality" | "distinct_leaves" | "distinct_stems" |
  "basic_data_colocation" | "mutation_kind"
- series: for event_locality, one of the read-cost series ("is_tx_read" |
  "is_tx_read_write" | "is_tx_read_any" | "is_block_read" | "is_block_read_write" |
  "is_block_read_any") or write-cost series ("is_tx_write" | "is_block_write"), each
  optionally paired with a "*_with_account" variant (same denominator, numerator
  restricted to touches whose account was also BASIC_DATA-accessed in the same scope;
  "is_tx_write" has no such variant -- see _event_locality_rows); for distinct_leaves/
  distinct_stems, "tx_write_counts" | "block_write_counts" | "reads"; for
  basic_data_colocation, "read" | "write"; for mutation_kind, the kind name
  ("insertion" | "update" | "deletion").
- granularity: "event" (row-weighted, no dedup) | "transaction" | "block"
- placement: "compact" | "current_anchored" | "n/a"
- S: int header window size, or -1 where not S-dependent (mutation_kind)
- value: float, a fraction in [0,1] for locality/co-location metrics, else a plain count
- denominator: float, the count backing a fraction; for plain-count metrics this just
  repeats `value` so the column is never implicitly empty

`distinct_leaves` values are computed once (leaf identity is invariant to S, see
keys.leaf_id) and then replicated across every S row so the schema stays uniform for the
consuming plotting code. `distinct_stems` emits two rows per (S, series, granularity) --
one per placement -- omitting `current_anchored` where S > 192 (see
keys.placement_valid_max_s); the two placements share the same numeric value because
stem identity does not depend on which suffix a low-index slot is given.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import numpy as np
import pandas as pd

from apx import basic_data, classify, replay
from apx.keys import PLACEMENT_COMPACT, PLACEMENT_CURRENT_ANCHORED, PLACEMENT_NA, placement_valid_max_s
from apx.normalize import normalize_addresses, normalize_addresses_and_slots

RESULT_COLUMNS = ["metric", "series", "granularity", "placement", "S", "value", "denominator"]

_FILES = {
    "storage_reads": "storage_reads_agg.parquet",
    "storage_tx_mutations": "storage_tx_mutations.parquet",
    "storage_block_mutations": "storage_block_mutations.parquet",
    "balance_reads": "balance_reads_agg.parquet",
    "nonce_reads": "nonce_reads_agg.parquet",
    "balance_block_mutations": "balance_block_mutations.parquet",
    "nonce_block_mutations": "nonce_block_mutations.parquet",
}


def _load_raw(data_dir: Path) -> dict[str, pd.DataFrame]:
    return {name: pd.read_parquet(data_dir / fname) for name, fname in _FILES.items()}


def _normalize_all(raw: dict[str, pd.DataFrame]) -> tuple[dict[str, pd.DataFrame], dict[str, dict]]:
    """Normalize every loaded table and collect rejection accounting per table."""
    clean: dict[str, pd.DataFrame] = {}
    rejects: dict[str, dict] = {}

    for name in ("storage_reads", "storage_tx_mutations", "storage_block_mutations"):
        clean[name], rejects[name] = normalize_addresses_and_slots(raw[name])

    for name in ("balance_reads", "nonce_reads", "balance_block_mutations", "nonce_block_mutations"):
        clean_df, n_rejected = normalize_addresses(raw[name])
        clean[name] = clean_df
        rejects[name] = {"address_rejected": n_rejected}

    return clean, rejects


def _fraction_rows(
    metric: str,
    series: str,
    granularity: str,
    placement: str,
    numerator: dict[int, float],
    denominator: dict[int, float] | float,
) -> list[dict]:
    rows = []
    for s, num in numerator.items():
        denom = denominator[s] if isinstance(denominator, dict) else denominator
        value = float("nan") if denom == 0 else num / denom
        rows.append(
            {
                "metric": metric,
                "series": series,
                "granularity": granularity,
                "placement": placement,
                "S": s,
                "value": value,
                "denominator": float(denom),
            }
        )
    return rows


def _count_rows(
    metric: str, series: str, granularity: str, placement: str, counts: dict[int, float]
) -> list[dict]:
    """Plain-count rows (leaf/stem replay, mutation-kind diagnostics): no natural
    denominator, so `denominator` repeats `value` per the results-table contract."""
    return [
        {
            "metric": metric,
            "series": series,
            "granularity": granularity,
            "placement": placement,
            "S": s,
            "value": float(v),
            "denominator": float(v),
        }
        for s, v in counts.items()
    ]


def _event_locality_rows(clean: dict[str, pd.DataFrame], reads: pd.DataFrame, s_values: list[int]) -> list[dict]:
    """Two cost-relevant series families, each an occurrence count (one row per distinct
    key touched, never weighted by how many times it was touched -- see classify.py and
    project-scope.md for why raw multiplicity doesn't map onto either cost).

    Reads model witness/proof cost, paid once per distinct key a block's execution
    touches. Writes model state-root rehash cost, paid once per distinct key net-changed
    in a block. Both get a plain occurrence curve ("pure": every touch, S-swept) and,
    where the data supports it, a "_with_account" curve sharing the same denominator but
    restricting the numerator to touches whose account also had an observed BASIC_DATA
    (balance/nonce) read or mutation in the same scope -- the only touches where sharing
    the account's header stem can actually save a proof lookup or a rehash; a slot
    touched without the account being independently touched gets no benefit from being
    in the header, regardless of S. `is_tx_write` has no such variant: only block-final
    balance/nonce mutations are extracted (no per-transaction table), so there is no way
    to check account co-mutation at transaction grain without overstating it via the
    block-level proxy.
    """
    rows: list[dict] = []
    ones = lambda df: np.ones(len(df), dtype=np.float64)  # noqa: E731

    reads_block = classify.classify_reads_block(reads, clean["storage_block_mutations"])
    read_proxy = basic_data.build_read_proxy(clean["balance_reads"], clean["nonce_reads"])
    read_proxy_block = read_proxy[["block_number", "address"]].drop_duplicates()
    mutation_proxy = basic_data.build_mutation_proxy(
        clean["balance_block_mutations"], clean["nonce_block_mutations"]
    )
    tx_join = ["block_number", "transaction_index", "address"]
    block_join = ["block_number", "address"]

    def add_pair(series_name: str, granularity: str, subset: pd.DataFrame, proxy, join_cols) -> None:
        weight = ones(subset)
        numerator, denom = replay.event_locality_curve(subset["slot"], weight, s_values)
        rows.extend(_fraction_rows("event_locality", series_name, granularity, PLACEMENT_NA, numerator, denom))
        if proxy is not None:
            matched, _ = basic_data.colocation_curve(subset, proxy, join_cols, weight, s_values)
            rows.extend(
                _fraction_rows(
                    "event_locality", f"{series_name}_with_account", granularity, PLACEMENT_NA, matched, denom
                )
            )

    tx_read_only = reads[~reads["is_write_coupled"]]
    tx_read_write = reads[reads["is_write_coupled"]]
    block_read_only = reads_block[~reads_block["is_write_coupled"]]
    block_read_write = reads_block[reads_block["is_write_coupled"]]

    add_pair("is_tx_read", "transaction", tx_read_only, read_proxy, tx_join)
    add_pair("is_tx_read_write", "transaction", tx_read_write, read_proxy, tx_join)
    add_pair("is_tx_read_any", "transaction", reads, read_proxy, tx_join)
    add_pair("is_block_read", "block", block_read_only, read_proxy_block, block_join)
    add_pair("is_block_read_write", "block", block_read_write, read_proxy_block, block_join)
    add_pair("is_block_read_any", "block", reads_block, read_proxy_block, block_join)

    add_pair("is_tx_write", "transaction", clean["storage_tx_mutations"], None, None)
    add_pair("is_block_write", "block", clean["storage_block_mutations"], mutation_proxy, block_join)

    return rows


def _distinct_leaf_rows(clean: dict[str, pd.DataFrame], reads: pd.DataFrame, s_values: list[int]) -> list[dict]:
    rows: list[dict] = []
    specs = [
        ("reads", "transaction", reads, ["block_number", "transaction_index", "address", "slot"]),
        ("reads", "block", reads, ["block_number", "address", "slot"]),
        ("tx_write_counts", "transaction", clean["storage_tx_mutations"], ["block_number", "transaction_index", "address", "slot"]),
        ("block_write_counts", "block", clean["storage_block_mutations"], ["block_number", "address", "slot"]),
    ]
    for series_name, granularity, df, group_cols in specs:
        count = replay.distinct_leaf_count(df, group_cols)
        counts = {s: count for s in s_values}
        rows += _count_rows("distinct_leaves", series_name, granularity, PLACEMENT_NA, counts)
    return rows


def _distinct_stem_rows(clean: dict[str, pd.DataFrame], reads: pd.DataFrame, s_values: list[int]) -> list[dict]:
    rows: list[dict] = []
    reads_block_dedup = reads.drop_duplicates(subset=["block_number", "address", "slot"])
    specs = [
        ("reads", "transaction", reads, ["block_number", "transaction_index"]),
        ("reads", "block", reads_block_dedup, ["block_number"]),
        ("tx_write_counts", "transaction", clean["storage_tx_mutations"], ["block_number", "transaction_index"]),
        ("block_write_counts", "block", clean["storage_block_mutations"], ["block_number"]),
    ]
    for series_name, granularity, df, unit_cols in specs:
        counts = replay.stem_counts(df, unit_cols, s_values)
        for placement in (PLACEMENT_COMPACT, PLACEMENT_CURRENT_ANCHORED):
            max_valid = placement_valid_max_s(placement)
            valid_counts = {s: v for s, v in counts.items() if s <= max_valid}
            rows += _count_rows("distinct_stems", series_name, granularity, placement, valid_counts)
    return rows


def _basic_data_rows(clean: dict[str, pd.DataFrame], reads: pd.DataFrame, s_values: list[int]) -> list[dict]:
    rows: list[dict] = []
    read_proxy = basic_data.build_read_proxy(clean["balance_reads"], clean["nonce_reads"])
    mutation_proxy = basic_data.build_mutation_proxy(
        clean["balance_block_mutations"], clean["nonce_block_mutations"]
    )

    read_weight = reads["read_count"].to_numpy(dtype=np.float64)
    matched, total = basic_data.colocation_curve(
        reads, read_proxy, basic_data.READ_PROXY_KEYS, read_weight, s_values
    )
    rows += _fraction_rows("basic_data_colocation", "read", "event", PLACEMENT_NA, matched, total)

    block_mut = clean["storage_block_mutations"]
    write_weight = np.ones(len(block_mut), dtype=np.float64)
    matched_w, total_w = basic_data.colocation_curve(
        block_mut, mutation_proxy, basic_data.MUTATION_PROXY_KEYS, write_weight, s_values
    )
    rows += _fraction_rows("basic_data_colocation", "write", "block", PLACEMENT_NA, matched_w, total_w)
    return rows


def _mutation_kind_rows(clean: dict[str, pd.DataFrame]) -> list[dict]:
    rows: list[dict] = []
    kinds = ["insertion", "update", "deletion"]
    for granularity, table_name in (("transaction", "storage_tx_mutations"), ("block", "storage_block_mutations")):
        table = clean[table_name]
        kind = classify.mutation_kind(table["from_value"], table["to_value"], hex_values=True)
        counts = kind.value_counts().reindex(kinds, fill_value=0)
        for kind_name, count in counts.items():
            rows.append(
                {
                    "metric": "mutation_kind",
                    "series": kind_name,
                    "granularity": granularity,
                    "placement": PLACEMENT_NA,
                    "S": -1,
                    "value": float(count),
                    "denominator": float(count),
                }
            )
    return rows


def build_results_table(data_dir: Path, s_values: Iterable[int] = range(254)) -> pd.DataFrame:
    data_dir = Path(data_dir)
    s_values = list(s_values)

    raw = _load_raw(data_dir)
    clean, _rejects = _normalize_all(raw)
    reads = classify.classify_reads(clean["storage_reads"], clean["storage_tx_mutations"])

    rows: list[dict] = []
    rows += _event_locality_rows(clean, reads, s_values)
    rows += _distinct_leaf_rows(clean, reads, s_values)
    rows += _distinct_stem_rows(clean, reads, s_values)
    rows += _basic_data_rows(clean, reads, s_values)
    rows += _mutation_kind_rows(clean)

    df = pd.DataFrame(rows, columns=RESULT_COLUMNS)
    df["S"] = df["S"].astype(int)
    df["value"] = df["value"].astype(float)
    df["denominator"] = df["denominator"].astype(float)
    return df


def validation_summary(data_dir: Path) -> dict:
    """Reconciliation checks required by project-scope.md: is_tx_read + is_tx_read_write
    = all reads (transaction grain) and is_block_read + is_block_read_write = all
    distinct block-touched reads (block grain), storage-mutation tables are unique on
    their natural key, `read_count` (still used to weight the `basic_data_colocation`
    "read" series) partitions consistently, and rejection counts are surfaced explicitly
    (never coerced to zero silently)."""
    data_dir = Path(data_dir)
    raw = _load_raw(data_dir)
    clean, rejects = _normalize_all(raw)
    reads = classify.classify_reads(clean["storage_reads"], clean["storage_tx_mutations"])
    reads_block = classify.classify_reads_block(reads, clean["storage_block_mutations"])

    summary: dict = {"rejected_counts": rejects}

    n_reads = len(reads)
    n_tx_read = int((~reads["is_write_coupled"]).sum())
    n_tx_read_write = int(reads["is_write_coupled"].sum())
    summary["read_partition_check"] = {
        "n_reads": n_reads,
        "n_tx_read": n_tx_read,
        "n_tx_read_write": n_tx_read_write,
        "partition_holds": n_tx_read + n_tx_read_write == n_reads,
    }

    n_block_reads = len(reads_block)
    n_block_read = int((~reads_block["is_write_coupled"]).sum())
    n_block_read_write = int(reads_block["is_write_coupled"].sum())
    summary["block_read_partition_check"] = {
        "n_block_reads": n_block_reads,
        "n_block_read": n_block_read,
        "n_block_read_write": n_block_read_write,
        "partition_holds": n_block_read + n_block_read_write == n_block_reads,
    }

    read_count_total = float(reads["read_count"].sum())
    read_count_split = float(reads.loc[~reads["is_write_coupled"], "read_count"].sum()) + float(
        reads.loc[reads["is_write_coupled"], "read_count"].sum()
    )
    summary["read_count_weighted_partition_check"] = {
        "total_read_count": read_count_total,
        "split_read_count": read_count_split,
        "partition_holds": bool(np.isclose(read_count_total, read_count_split)),
    }

    # Named after the source table (not a report-facing series name): the same
    # uniqueness fact backs both the event_locality is_tx_write/is_block_write series
    # and the distinct_leaves/distinct_stems tx_write_counts/block_write_counts series,
    # so tying this key to either one's current name would go stale the next time either
    # metric's naming changes.
    summary["storage_tx_mutations_key_unique"] = bool(
        not clean["storage_tx_mutations"]
        .duplicated(subset=["block_number", "transaction_index", "address", "slot"])
        .any()
    )
    summary["storage_block_mutations_key_unique"] = bool(
        not clean["storage_block_mutations"]
        .duplicated(subset=["block_number", "address", "slot"])
        .any()
    )
    return summary
