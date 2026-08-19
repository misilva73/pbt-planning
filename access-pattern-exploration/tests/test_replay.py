import numpy as np
import pandas as pd

from apx.replay import (
    cumulative_count_below,
    distinct_leaf_count,
    event_locality_curve,
    stem_counts,
)


def _slot_hex(v: int) -> str:
    return f"0x{v:064x}"


def test_cumulative_count_below_hand_computed():
    # values: two at 0, one at 5, one at s_max+1 (sentinel, must never count).
    bucket = np.array([0, 0, 5, 4], dtype=np.int64)  # s_max = 3, sentinel = 4
    weight = np.array([1.0, 2.0, 10.0, 999.0], dtype=np.float64)
    out = cumulative_count_below(bucket, weight, s_max=3)
    # out[S] = sum(weight[bucket < S]) for S = 0..3
    assert out[0] == 0.0  # nothing is < 0
    assert out[1] == 3.0  # the two zeros (1 + 2)
    assert out[2] == 3.0  # still just the zeros (5 and the sentinel are >= 2)
    assert out[3] == 3.0  # 5 is not < 3 either
    assert len(out) == 4


def test_event_locality_curve_hand_computed():
    slots = pd.Series([_slot_hex(0), _slot_hex(5), _slot_hex(63), _slot_hex(64), _slot_hex(300)])
    weight = np.array([1.0, 1.0, 1.0, 1.0, 1.0])
    numerator, total = event_locality_curve(slots, weight, s_values=[0, 1, 64, 253])
    assert total == 5.0
    assert numerator[0] == 0.0  # nothing < 0
    assert numerator[1] == 1.0  # only slot 0
    assert numerator[64] == 3.0  # slots 0, 5, 63 are < 64; 64 and 300 are not
    assert numerator[253] == 4.0  # 300 is the only one >= 253


def test_event_locality_curve_is_weighted():
    slots = pd.Series([_slot_hex(1), _slot_hex(100)])
    weight = np.array([3.0, 7.0])
    numerator, total = event_locality_curve(slots, weight, s_values=[0, 2, 50])
    assert total == 10.0
    assert numerator[2] == 3.0  # only the weight-3 event has slot < 2
    assert numerator[50] == 3.0  # slot 100 still not < 50


def test_distinct_leaf_count_dedups_within_unit():
    df = pd.DataFrame(
        {
            "block_number": [1, 1, 1, 2],
            "transaction_index": [0, 0, 1, 0],
            "address": ["0xa", "0xa", "0xa", "0xa"],
            "slot": ["0x1", "0x1", "0x1", "0x1"],  # same slot, repeated
        }
    )
    # Per-transaction dedup: (1,0,a,1) once, (1,1,a,1) once, (2,0,a,1) once -> 3.
    assert distinct_leaf_count(df, ["block_number", "transaction_index", "address", "slot"]) == 3
    # Per-block dedup: (1,a,1) once, (2,a,1) once -> 2.
    assert distinct_leaf_count(df, ["block_number", "address", "slot"]) == 2


def test_stem_counts_hand_computed():
    # See module docstring / PR description for the by-hand derivation of these numbers.
    # unit1 = (block=1, tx=1): addrA touches low slots {5, 10}; addrB touches high slots
    #   {300, 500}, both tree_index 1 (300 // 256 == 500 // 256 == 1).
    # unit2 = (block=1, tx=2): addrA touches low slots {70, 5}; addrC touches high slots
    #   {256, 600} with distinct tree_index 1 and 2 respectively.
    rows = [
        (1, 1, "A", 5),
        (1, 1, "A", 10),
        (1, 1, "B", 300),
        (1, 1, "B", 500),
        (1, 2, "A", 70),
        (1, 2, "A", 5),
        (1, 2, "C", 256),
        (1, 2, "C", 600),
    ]
    df = pd.DataFrame(
        [
            {"block_number": b, "transaction_index": t, "address": a, "slot": _slot_hex(s)}
            for b, t, a, s in rows
        ]
    )
    counts = stem_counts(df, ["block_number", "transaction_index"], s_values=[0, 64, 253])
    assert counts[0] == 5.0
    assert counts[64] == 6.0
    assert counts[253] == 5.0
