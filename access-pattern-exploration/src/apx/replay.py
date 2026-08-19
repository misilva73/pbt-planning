"""S-sweep event-locality curves and Tier-1 leaf/stem replay counts.

This is the performance-sensitive module: naively recomputing a groupby once per S in
0..253 over tens of millions of rows does not scale. Every function here instead does a
single O(n) pass to build a small per-key summary, then answers the whole S sweep from
that summary in O(S_max) using cumulative histograms -- no per-S groupby.

Two structural facts make this possible:

- Distinct-leaf counts never depend on S (see keys.leaf_id), so they are computed once.
- Distinct-stem counts depend on S only through, for each (unit, address) pair, whether
  its touched slots in [0, 255] include one < S (a header-stem leaf) and one >= S (a
  storage-zone leaf with tree_index 0). Slots >= 256 always contribute their own
  S-invariant tree_index groups, because STEM_SUBTREE_WIDTH (256) exceeds MAX_SWEEP_S
  (253) -- the header window can never reach slot 256. So per (unit, address) we only
  need three numbers: min touched slot in [0,255] ("min_low"), max touched slot in
  [0,255] ("max_low"), and the count of distinct tree_index groups among slots >= 256
  ("n_high"). See `_stem_group_stats` and `stem_counts` for the derivation.
"""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd

from apx.keys import MAX_SWEEP_S, slot_low_and_group_key


def cumulative_count_below(bucket: np.ndarray, weight: np.ndarray, s_max: int) -> np.ndarray:
    """out[S] = sum(weight[bucket < S]) for S = 0..s_max (length s_max + 1).

    Callers encode "never counts for any S in range" as bucket >= s_max + 1.
    """
    hist = np.bincount(bucket, weights=weight, minlength=s_max + 2)[: s_max + 2]
    cum = np.concatenate(([0.0], np.cumsum(hist)))
    return cum[: s_max + 1]


def _select(curve: np.ndarray, s_values: Iterable[int]) -> dict[int, float]:
    return {s: float(curve[s]) for s in s_values}


def event_locality_curve(
    slot_hex: pd.Series, weight: np.ndarray, s_values: Iterable[int]
) -> tuple[dict[int, float], float]:
    """Return ({S: events with slot < S}, total_events) for a row-weighted series.

    `weight` is read_count for read series or an array of ones for row-count series
    (tx_write_counts / block_write_counts / is_tx_read* variants).
    """
    s_values = list(s_values)
    s_max = max(s_values) if s_values else 0
    slot_low, _ = slot_low_and_group_key(slot_hex)
    bucket = slot_low.fillna(s_max + 1).to_numpy(dtype=np.int64)
    weight = np.asarray(weight, dtype=np.float64)
    curve = cumulative_count_below(bucket, weight, s_max)
    return _select(curve, s_values), float(weight.sum())


def distinct_leaf_count(df: pd.DataFrame, group_cols: list[str]) -> int:
    """Distinct-leaf replay count: unique (unit, address, slot) rows.

    Leaf identity is (address, slot), invariant to S (see keys.leaf_id); `group_cols`
    fixes the replay unit (transaction or block) that "distinct" is computed within,
    e.g. ["block_number", "transaction_index", "address", "slot"] for per-transaction
    dedup, or ["block_number", "address", "slot"] for per-block dedup.
    """
    return int(df.drop_duplicates(subset=group_cols).shape[0])


def _stem_group_stats(df: pd.DataFrame, unit_cols: list[str]) -> pd.DataFrame:
    """Per (unit, address) summary needed for the whole S sweep: min/max touched slot
    restricted to [0, 255] ("_low"), and the count of distinct tree_index groups among
    slots >= 256 ("n_high"). One groupby, independent of S.
    """
    slot_low, tree_index_key = slot_low_and_group_key(df["slot"])
    work = df[[*unit_cols, "address"]].copy()
    work["slot_low"] = slot_low
    work["tree_index_key"] = tree_index_key.where(slot_low.isna())

    group_cols = [*unit_cols, "address"]
    low_stats = work.groupby(group_cols, sort=False)["slot_low"].agg(["min", "max"])
    low_stats.columns = ["min_low", "max_low"]

    high_rows = work[work["slot_low"].isna()]
    n_high = (
        high_rows.groupby(group_cols, sort=False)["tree_index_key"]
        .nunique()
        .reindex(low_stats.index, fill_value=0)
    )
    low_stats["n_high"] = n_high
    return low_stats.reset_index()


def stem_counts(df: pd.DataFrame, unit_cols: list[str], s_values: Iterable[int]) -> dict[int, float]:
    """Distinct-stem replay count summed across all units, for every S in `s_values`.

    Per (unit, address) group: a header stem exists at S iff min_low < S; a storage-zone
    tree_index=0 stem exists at S iff max_low >= S (both restricted to touched slots in
    [0, 255], see module docstring); n_high storage-zone stems always exist, independent
    of S. Summed across all (unit, address) groups via two cumulative histograms rather
    than per-S boolean scans.
    """
    s_values = list(s_values)
    s_max = max(s_values) if s_values else 0
    stats = _stem_group_stats(df, unit_cols)
    n_groups = len(stats)
    ones = np.ones(n_groups, dtype=np.float64)

    # Header-stem contribution: count(min_low < S). Missing (-> no low slot at all in
    # this group) is sentinel s_max+1, which is never < any S in [0, s_max].
    min_low_bucket = stats["min_low"].fillna(s_max + 1).to_numpy(dtype=np.int64)
    header_curve = cumulative_count_below(min_low_bucket, ones, s_max)

    # Tree_index=0 contribution: count(max_low >= S) = n_groups - count(max_low < S).
    # Missing max_low must never satisfy ">= S" for any S >= 0, so its bucket is shifted
    # to 0 (i.e. "max_low == -1"), which is < every S+1 threshold used below.
    max_low_bucket = (stats["max_low"].fillna(-1) + 1).to_numpy(dtype=np.int64)
    lt_curve = cumulative_count_below(max_low_bucket, ones, s_max + 1)  # indexed by S+1

    n_high_total = float(stats["n_high"].sum())

    out: dict[int, float] = {}
    for s in s_values:
        tree0 = n_groups - lt_curve[s + 1]
        out[s] = float(header_curve[s] + tree0 + n_high_total)
    return out
