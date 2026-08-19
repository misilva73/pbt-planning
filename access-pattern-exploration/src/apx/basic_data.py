"""Observed-BASIC_DATA co-location proxy (project-scope.md).

A BASIC_DATA-read proxy key is a (block, transaction_index, address) observed in either
balance or nonce reads. A BASIC_DATA-mutation proxy key is a (block, address) observed in
either balance or nonce block-final mutations. Both are lower bounds on "this account's
header was also touched in the same unit": they miss implied header reads/writes such as
code-hash resolution and account-existence checks that never surface as a balance/nonce
row. Report both channels alongside, never inferred from storage access alone.
"""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd

from apx.keys import slot_low_and_group_key
from apx.replay import cumulative_count_below

READ_PROXY_KEYS = ["block_number", "transaction_index", "address"]
MUTATION_PROXY_KEYS = ["block_number", "address"]


def build_read_proxy(balance_reads: pd.DataFrame, nonce_reads: pd.DataFrame) -> pd.DataFrame:
    """Union of (block, transaction_index, address) keys seen in balance or nonce reads."""
    return pd.concat(
        [balance_reads[READ_PROXY_KEYS], nonce_reads[READ_PROXY_KEYS]], ignore_index=True
    ).drop_duplicates()


def build_mutation_proxy(
    balance_mutations: pd.DataFrame, nonce_mutations: pd.DataFrame
) -> pd.DataFrame:
    """Union of (block, address) keys seen in balance or nonce block-final mutations."""
    return pd.concat(
        [balance_mutations[MUTATION_PROXY_KEYS], nonce_mutations[MUTATION_PROXY_KEYS]],
        ignore_index=True,
    ).drop_duplicates()


def colocation_curve(
    storage_df: pd.DataFrame,
    proxy: pd.DataFrame,
    join_cols: list[str],
    weight: np.ndarray,
    s_values: Iterable[int],
) -> tuple[dict[int, float], dict[int, float]]:
    """Return ({S: matched weight}, {S: total weight}) for low-index (slot < S) storage
    events, where "matched" means the row's `join_cols` key is present in `proxy`.

    Both curves vary with S because the low-index population itself grows with S; the
    caller divides matched/total per S and must expose total as the fraction's
    denominator rather than hiding it.
    """
    s_values = list(s_values)
    s_max = max(s_values) if s_values else 0

    marker = proxy[join_cols].drop_duplicates().assign(_matched=True)
    merged = storage_df.merge(marker, on=join_cols, how="left")
    matched = merged["_matched"].fillna(False).to_numpy(dtype=bool)

    slot_low, _ = slot_low_and_group_key(storage_df["slot"])
    bucket = slot_low.fillna(s_max + 1).to_numpy(dtype=np.int64)
    weight = np.asarray(weight, dtype=np.float64)

    total_curve = cumulative_count_below(bucket, weight, s_max)
    matched_curve = cumulative_count_below(bucket, weight * matched, s_max)

    total = {s: float(total_curve[s]) for s in s_values}
    matched_out = {s: float(matched_curve[s]) for s in s_values}
    return matched_out, total
