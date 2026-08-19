import pandas as pd

from apx import keys


def test_stem_id_header_vs_storage():
    # Slot below the window lives in the account's single header stem.
    assert keys.stem_id("0xaa", 5, s_value=64) == ("header", "0xaa")
    # Slot at or above the window falls back to the current storage-zone derivation.
    assert keys.stem_id("0xaa", 64, s_value=64) == ("storage", "0xaa", 64 // 256)
    assert keys.stem_id("0xaa", 300, s_value=64) == ("storage", "0xaa", 1)
    # Growing S never renumbers an overflow slot's tree_index.
    assert keys.stem_id("0xaa", 300, s_value=0) == ("storage", "0xaa", 1)
    assert keys.stem_id("0xaa", 300, s_value=253) == ("storage", "0xaa", 1)


def test_leaf_id_is_s_invariant():
    assert keys.leaf_id("0xaa", 5) == keys.leaf_id("0xaa", 5)
    assert keys.leaf_id("0xaa", 5) != keys.leaf_id("0xaa", 6)
    # Same tuple regardless of any S value, since leaf_id doesn't even take S.
    assert keys.leaf_id("0xaa", 300) == ("0xaa", 300)


def test_placement_suffixes_and_validity():
    assert keys.compact_suffix(0) == 3
    assert keys.compact_suffix(252) == 255
    assert keys.current_anchored_suffix(0) == 64
    assert keys.current_anchored_suffix(63) == 127  # matches live S=64 layout exactly
    assert keys.placement_valid_max_s(keys.PLACEMENT_COMPACT) == 253
    assert keys.placement_valid_max_s(keys.PLACEMENT_CURRENT_ANCHORED) == 192


def test_slot_low_and_group_key_hand_computed():
    # 5 -> low value 5. 255 -> low value 255 (boundary of "low"). 256 -> not low (boundary
    # of "high", tree_index 1). 300 -> not low, tree_index 300 // 256 == 1, same group as
    # 256. 600 -> not low, tree_index 600 // 256 == 2, a different group from 256/300.
    values = [5, 255, 256, 300, 600]
    slot_hex = pd.Series([f"0x{v:064x}" for v in values])
    slot_low, group_key = keys.slot_low_and_group_key(slot_hex)

    assert slot_low.iloc[0] == 5 and slot_low.iloc[1] == 255
    assert slot_low.iloc[2:].isna().all()
    assert group_key.iloc[2] == group_key.iloc[3]  # 256 and 300 share tree_index 1
    assert group_key.iloc[2] != group_key.iloc[4]  # 256 and 600 differ (tree_index 1 vs 2)
