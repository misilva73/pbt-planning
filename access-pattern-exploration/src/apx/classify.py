"""Read classification (read-only vs. write-coupled) and mutation-kind diagnostics.

Per project-scope.md: a storage-read event is write-coupled if its
(block_number, transaction_index, address, slot) key also appears in the transaction
mutation set (which already excludes no-ops); otherwise it is read-only. These two
series are disjoint and must partition every read event.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

JOIN_KEYS = ["block_number", "transaction_index", "address", "slot"]
BLOCK_JOIN_KEYS = ["block_number", "address", "slot"]


def classify_reads(reads: pd.DataFrame, tx_mutations: pd.DataFrame) -> pd.DataFrame:
    """Return `reads` with an added boolean `is_write_coupled` column.

    A row is write-coupled iff its (block, transaction, address, slot) key appears in
    `tx_mutations` (already non-no-op by construction of storage_tx_mutations.parquet).
    Implemented as a left-join existence check: `tx_mutations` is already unique on
    JOIN_KEYS (one row per mutated key), so the merge cannot duplicate any read row.
    """
    marker = tx_mutations[JOIN_KEYS].drop_duplicates().assign(_is_write_coupled=True)
    merged = reads.merge(marker, on=JOIN_KEYS, how="left")
    out = reads.copy()
    out["is_write_coupled"] = merged["_is_write_coupled"].fillna(False).astype(bool).to_numpy()
    return out


def classify_reads_block(reads: pd.DataFrame, block_mutations: pd.DataFrame) -> pd.DataFrame:
    """Dedup `reads` to one row per (block, address, slot) -- read by any transaction in
    the block -- and add a boolean `is_write_coupled` column: True iff that key also
    appears in `block_mutations` (net-changed somewhere in the block).

    This is the block-granularity counterpart to `classify_reads`: a slot read in tx 3
    and tx 7 of the same block is one row here, since the header-window benefit for a
    block-final state-root update only cares about distinct (address, slot) keys, not
    which transaction(s) touched them.
    """
    block_keys = reads[BLOCK_JOIN_KEYS].drop_duplicates().reset_index(drop=True)
    marker = block_mutations[BLOCK_JOIN_KEYS].drop_duplicates().assign(_is_write_coupled=True)
    merged = block_keys.merge(marker, on=BLOCK_JOIN_KEYS, how="left")
    out = block_keys.copy()
    out["is_write_coupled"] = merged["_is_write_coupled"].fillna(False).astype(bool).to_numpy()
    return out


def parse_int_value(value: str, base: int) -> int:
    """Parse a single from_value/to_value string as an integer in the given base."""
    return int(value, base)


def _parse_int_series(series: pd.Series, base: int) -> pd.Series:
    if base == 16:
        return series.map(lambda v: int(v, 16))
    # Decimal strings or already-numeric (e.g. nonce arrives as native uint64).
    return pd.to_numeric(series, errors="raise").astype("int64")


def mutation_kind(from_value: pd.Series, to_value: pd.Series, *, hex_values: bool) -> pd.Series:
    """Classify each mutation row as insertion / update / deletion.

    insertion: from == 0, to != 0.  update: from != 0, to != 0.  deletion: from != 0,
    to == 0. from == to (a no-op) is assumed already excluded upstream (storage_tx/
    block_mutations.parquet both drop no-ops via their query's HAVING clause); such a
    row would fall through to "update" here since it is not classifiable as insertion or
    deletion, so callers should not feed no-op rows into this function.
    """
    base = 16 if hex_values else 10
    from_int = _parse_int_series(from_value, base)
    to_int = _parse_int_series(to_value, base)
    from_zero = from_int == 0
    to_zero = to_int == 0
    kind = np.where(from_zero & ~to_zero, "insertion", np.where(~from_zero & to_zero, "deletion", "update"))
    return pd.Series(kind, index=from_value.index, name="mutation_kind")
