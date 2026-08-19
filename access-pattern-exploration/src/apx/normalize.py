"""Address/slot normalization and rejection accounting.

Per project-scope.md: normalize addresses to lowercase fixed-width 20-byte hex and slots
to unsigned 256-bit hex before any join or classification; malformed or out-of-range
values are excluded from analysis but their count is always reported, never silently
coerced to zero or dropped without accounting.
"""

from __future__ import annotations

import re

import pandas as pd

_ADDRESS_RE = re.compile(r"^0x[0-9a-f]{40}$")
_SLOT_RE = re.compile(r"^0x[0-9a-f]{64}$")


def _validate(series: pd.Series, pattern: re.Pattern) -> tuple[pd.Series, int]:
    """Lowercase `series` and keep only values matching `pattern`.

    Returns (valid-and-lowercased subset, n_rejected). The rejected count covers
    non-string input, wrong length, and non-hex characters alike.
    """
    lowered = series.astype("string").str.lower()
    valid_mask = lowered.str.match(pattern).fillna(False)
    n_rejected = int((~valid_mask).sum())
    return lowered[valid_mask], n_rejected


def normalize_address_column(series: pd.Series) -> tuple[pd.Series, int]:
    """Validate a column of `0x`+40-hex address strings. See `_validate`."""
    return _validate(series, _ADDRESS_RE)


def normalize_slot_column(series: pd.Series) -> tuple[pd.Series, int]:
    """Validate a column of `0x`+64-hex (unsigned 256-bit) slot strings. See `_validate`."""
    return _validate(series, _SLOT_RE)


def normalize_addresses(df: pd.DataFrame, column: str = "address") -> tuple[pd.DataFrame, int]:
    """Normalize the address column of an account-level table (balance/nonce reads or
    mutations). Rows with a malformed address are dropped; their count is returned."""
    cleaned, n_rejected = normalize_address_column(df[column])
    out = df.loc[cleaned.index].copy()
    out[column] = cleaned
    return out.reset_index(drop=True), n_rejected


def normalize_addresses_and_slots(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """Normalize both `address` and `slot` columns of a storage-shaped table.

    A row is kept only if both columns are well-formed; the two rejection counts are
    reported separately so a slot-shaped failure is never mistaken for an address-shaped
    one (or vice versa).
    """
    addr_clean, n_addr_rejected = normalize_address_column(df["address"])
    slot_clean, n_slot_rejected = normalize_slot_column(df["slot"])
    valid_index = addr_clean.index.intersection(slot_clean.index)
    out = df.loc[valid_index].copy()
    out["address"] = addr_clean.loc[valid_index]
    out["slot"] = slot_clean.loc[valid_index]
    rejected = {"address_rejected": n_addr_rejected, "slot_rejected": n_slot_rejected}
    return out.reset_index(drop=True), rejected
