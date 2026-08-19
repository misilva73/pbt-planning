"""PBT account-header key-derivation constants and stem/leaf identity.

See knowledge-base/03-key-derivation.md for the authoritative derivation this mirrors.
All identity here is placement-independent: which suffix byte a low-index slot is given
inside the header (compact vs. current-anchored) never changes which stem or leaf it
belongs to -- only the numeric suffix used to reach it. Placement therefore only affects
*validity* (which S values a placement can express), never the stem/leaf counts.
"""

from __future__ import annotations

import pandas as pd

STEM_SUBTREE_WIDTH = 256
HEADER_STORAGE_SLOTS = 64  # current EIP-8297 S

# One-byte header suffix has 256 values; 3 are reserved (BASIC_DATA, CODE_HASH,
# DELEGATION), so at most 253 values are allocatable to storage slots when C=0.
MAX_SWEEP_S = 253

PLACEMENT_COMPACT = "compact"
PLACEMENT_CURRENT_ANCHORED = "current_anchored"
PLACEMENT_NA = "n/a"


def compact_suffix(slot_low: int) -> int:
    """Header suffix for low-index slot `slot_low` under the compact placement."""
    return 3 + slot_low


def current_anchored_suffix(slot_low: int) -> int:
    """Header suffix for low-index slot `slot_low` under the current-anchored placement
    (suffix 64..127 for S=64 matches the live EIP-8297 layout exactly)."""
    return 64 + slot_low


def placement_valid_max_s(placement: str) -> int:
    """Largest S at which `placement` can express every slot 0..S-1 within one byte."""
    if placement == PLACEMENT_COMPACT:
        return 253
    if placement == PLACEMENT_CURRENT_ANCHORED:
        return 192
    raise ValueError(f"unknown placement: {placement!r}")


def leaf_id(address: str, slot_int: int) -> tuple[str, int]:
    """Leaf identity for a touched storage slot: invariant to S and to placement.

    Every touched (address, slot) needs exactly one leaf whether it lives in the header
    or the storage zone, so distinct-leaf counts never depend on the header window size.
    """
    return (address, slot_int)


def stem_id(address: str, slot_int: int, s_value: int) -> tuple:
    """Stem identity for a touched storage slot under header window size `s_value`.

    If slot_int < s_value, the slot lives in the account's single header stem.
    Otherwise it lives in the storage zone, grouped by tree_index = slot // 256;
    changing s_value never renumbers overflow slots (per project-scope.md).
    """
    if slot_int < s_value:
        return ("header", address)
    return ("storage", address, slot_int // STEM_SUBTREE_WIDTH)


_HEX_BYTE_LOOKUP = {f"{i:02x}": i for i in range(256)}


def slot_low_and_group_key(slot_hex: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Split normalized `0x`+64-hex slot strings into a fast (low value, tree_index key)
    pair, without ever parsing a full 256-bit integer.

    `slot_low` is the slot's integer value (0..255, nullable Int64) when that value is
    < STEM_SUBTREE_WIDTH (256), else <NA>. `tree_index_key` is a string that is equal for
    two slots iff they share tree_index = slot // STEM_SUBTREE_WIDTH -- obtained by
    slicing off the low hex byte rather than computing a big-integer floor division, since
    hex is a fixed-width, big-endian encoding and STEM_SUBTREE_WIDTH is exactly one byte
    (256 = 16**2). Only meaningful/used for rows where `slot_low` is <NA> (slot >= 256).

    The maximum swept S (MAX_SWEEP_S = 253) is below STEM_SUBTREE_WIDTH, so callers never
    need `tree_index_key` for slots the sweep could place in the header; see replay.py.
    """
    high_part = slot_hex.str.slice(2, -2)  # 62 hex chars above the low byte
    low_hex = slot_hex.str.slice(-2)
    is_low = high_part == "0" * 62
    low_value = low_hex.map(_HEX_BYTE_LOOKUP).astype("Int64")
    slot_low = low_value.where(is_low)
    return slot_low, high_part
