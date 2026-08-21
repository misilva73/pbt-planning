"""Synthetic Part 1 results table matching the fixed apx.pipeline.build_results_table contract.

The analytical core (apx.pipeline) is being built by a parallel agent. This fixture lets
the plotting/report layer be developed and tested against the same schema without waiting
for that code to land. Keep it in sync with the contract in project-scope.md /
the task brief, not with whatever apx.pipeline actually emits.
"""

from __future__ import annotations

import pandas as pd

# A reduced but representative S sweep: dense enough to look like a curve, sparse enough
# to keep the fixture at a few hundred rows. Always includes the emphasized set.
EMPHASIZED_S = [0, 8, 16, 32, 64, 96, 128, 192, 253]
S_VALUES = sorted(set(range(0, 254, 12)) | set(EMPHASIZED_S))

EVENT_LOCALITY_SERIES = [
    "is_tx_touched",
    "is_block_touched",
    "is_tx_touched_with_account",
    "is_block_touched_with_account",
    "is_tx_write",
    "is_block_write",
    "is_block_write_with_account",
]
EVENT_LOCALITY_GRANULARITY = {
    "is_tx_touched": "transaction",
    "is_block_touched": "block",
    "is_tx_touched_with_account": "transaction",
    "is_block_touched_with_account": "block",
    "is_tx_write": "transaction",
    "is_block_write": "block",
    "is_block_write_with_account": "block",
}
# Fixed per-series denominators (total events in that series across the whole sample).
# "_with_account" variants share their pure counterpart's denominator by construction
# (same population, narrower numerator) -- see pipeline._event_locality_rows.
EVENT_LOCALITY_DENOMINATOR = {
    "is_tx_touched": 5_000_000.0,
    "is_block_touched": 4_200_000.0,
    "is_tx_touched_with_account": 5_000_000.0,
    "is_block_touched_with_account": 4_200_000.0,
    "is_tx_write": 700_000.0,
    "is_block_write": 400_000.0,
    "is_block_write_with_account": 400_000.0,
}

LEAF_STEM_SERIES_GRANULARITY = [
    ("reads", "transaction"),
    ("reads", "block"),
    ("tx_write_counts", "transaction"),
    ("block_write_counts", "block"),
]

PLACEMENTS = ["compact", "current_anchored"]


def _saturating_fraction(s: int, denom_scale: float) -> float:
    """Monotonically non-decreasing fraction in [0, 1], saturating as S grows."""
    if s <= 0:
        return 0.0
    value = 1 - pow(2.718281828, -s / denom_scale)
    return min(round(value, 6), 1.0)


def _placement_valid(placement: str, s: int) -> bool:
    if placement == "current_anchored":
        return s <= 192
    return True


def _event_locality_rows() -> list[dict]:
    rows = []
    for series in EVENT_LOCALITY_SERIES:
        granularity = EVENT_LOCALITY_GRANULARITY[series]
        denom = EVENT_LOCALITY_DENOMINATOR[series]
        # vary the saturation rate a bit per series so curves aren't identical
        scale = 40.0 + 10.0 * EVENT_LOCALITY_SERIES.index(series)
        for s in S_VALUES:
            frac = _saturating_fraction(s, scale)
            rows.append(
                {
                    "metric": "event_locality",
                    "series": series,
                    "granularity": granularity,
                    "placement": "n/a",
                    "S": s,
                    "value": frac,
                    "denominator": denom,
                }
            )
    return rows


def _leaf_rows() -> list[dict]:
    """Distinct leaf counts: invariant to S by construction (flat reference line)."""
    rows = []
    base_counts = {
        ("reads", "transaction"): 2_000_000.0,
        ("reads", "block"): 1_500_000.0,
        ("tx_write_counts", "transaction"): 600_000.0,
        ("block_write_counts", "block"): 350_000.0,
    }
    for (series, granularity), count in base_counts.items():
        for s in S_VALUES:
            rows.append(
                {
                    "metric": "distinct_leaves",
                    "series": series,
                    "granularity": granularity,
                    "placement": "n/a",
                    "S": s,
                    "value": count,
                    "denominator": count,
                }
            )
    return rows


def _stem_rows() -> list[dict]:
    """Distinct stem counts: decrease as S grows (more slots co-located under fewer header
    stems), plateauing; two rows per (S, series, granularity), one per valid placement."""
    rows = []
    base_counts = {
        ("reads", "transaction"): 1_900_000.0,
        ("reads", "block"): 1_400_000.0,
        ("tx_write_counts", "transaction"): 580_000.0,
        ("block_write_counts", "block"): 330_000.0,
    }
    for (series, granularity), start_count in base_counts.items():
        for placement in PLACEMENTS:
            for s in S_VALUES:
                if not _placement_valid(placement, s):
                    continue
                # more of the window collapses into shared header stems as S grows
                reduction = start_count * 0.35 * (1 - pow(2.718281828, -s / 60.0))
                # current_anchored groups slightly less efficiently than compact
                penalty = 1.02 if placement == "current_anchored" else 1.0
                value = round((start_count - reduction) * penalty, 2)
                rows.append(
                    {
                        "metric": "distinct_stems",
                        "series": series,
                        "granularity": granularity,
                        "placement": placement,
                        "S": s,
                        "value": value,
                        "denominator": value,
                    }
                )
    return rows


def _basic_data_colocation_rows() -> list[dict]:
    rows = []
    denom = {"read": 4_500_000.0, "write": 1_100_000.0}
    granularity = {"read": "transaction", "write": "block"}
    for series in ("read", "write"):
        for s in S_VALUES:
            frac = _saturating_fraction(s, 50.0 if series == "read" else 70.0)
            rows.append(
                {
                    "metric": "basic_data_colocation",
                    "series": series,
                    "granularity": granularity[series],
                    "placement": "n/a",
                    "S": s,
                    "value": frac,
                    "denominator": denom[series],
                }
            )
    return rows


def _mutation_kind_rows() -> list[dict]:
    rows = []
    counts = {"insertion": 250_000.0, "update": 900_000.0, "deletion": 150_000.0}
    for series, count in counts.items():
        for granularity in ("transaction", "block"):
            # transaction-level sensitivity counts slightly more (incremental updates)
            value = count * (1.1 if granularity == "transaction" else 1.0)
            rows.append(
                {
                    "metric": "mutation_kind",
                    "series": series,
                    "granularity": granularity,
                    "placement": "n/a",
                    "S": -1,
                    "value": round(value, 2),
                    "denominator": round(value, 2),
                }
            )
    return rows


def synthetic_results_table() -> pd.DataFrame:
    """Build a tidy results table matching the apx.pipeline.build_results_table contract."""
    rows = (
        _event_locality_rows()
        + _leaf_rows()
        + _stem_rows()
        + _basic_data_colocation_rows()
        + _mutation_kind_rows()
    )
    df = pd.DataFrame(rows)
    columns = ["metric", "series", "granularity", "placement", "S", "value", "denominator"]
    return df[columns]


def synthetic_validation() -> dict:
    """A small reconciliation dict of the dict[str, Any] shape build_report should render."""
    return {
        "source_rows": 21_621_719_717,
        "accepted_rows": 21_621_719_001,
        "rejected_rows": 716,
        "reads_and_writes_are_disjoint": True,
        "block_net_keys_unique": True,
        "notes": [
            "all reported fractions carry a non-hidden denominator",
            "transaction ordering validated against canonical_execution_transaction",
        ],
    }
