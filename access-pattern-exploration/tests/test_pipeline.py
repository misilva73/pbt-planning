"""End-to-end tests against a tiny, representative parquet dataset.

The production pilot contains tens of millions of rows and is intentionally not part of
the unit-test suite.  These fixtures preserve the same file schemas and exercise the
complete load/normalize/classify/replay pipeline without making local test runs depend on
multi-gigabyte, uncommitted data.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from apx import classify
from apx.pipeline import (
    RESULT_COLUMNS,
    _load_raw,
    _normalize_all,
    build_results_table,
    validation_summary,
)


def _address(byte: str) -> str:
    return "0x" + byte * 40


def _slot(value: int) -> str:
    return f"0x{value:064x}"


@pytest.fixture(scope="module")
def data_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Write all seven pipeline inputs with a handful of coherent rows."""
    path = tmp_path_factory.mktemp("pipeline-data")
    address_a = _address("1")
    address_b = _address("2")
    address_c = _address("A")  # normalization should lowercase this address

    tables = {
        "storage_reads_agg.parquet": pd.DataFrame(
            [
                (1, 0, address_a, _slot(0), 3),
                (1, 0, address_a, _slot(8), 1),
                (1, 1, address_b, _slot(64), 2),
                (2, 0, address_a, _slot(300), 4),
                (2, 1, address_c, _slot(1), 1),
            ],
            columns=["block_number", "transaction_index", "address", "slot", "read_count"],
        ),
        "storage_tx_mutations.parquet": pd.DataFrame(
            [
                (1, 0, address_a, _slot(0), _slot(0), _slot(1), 1),
                (1, 1, address_b, _slot(64), _slot(2), _slot(3), 1),
                (2, 0, address_a, _slot(300), _slot(4), _slot(0), 1),
            ],
            columns=[
                "block_number",
                "transaction_index",
                "address",
                "slot",
                "from_value",
                "to_value",
                "n_diffs",
            ],
        ),
        "storage_block_mutations.parquet": pd.DataFrame(
            [
                (1, address_a, _slot(0), _slot(0), _slot(1), 1),
                (1, address_b, _slot(64), _slot(2), _slot(3), 1),
                (2, address_a, _slot(300), _slot(4), _slot(0), 1),
            ],
            columns=["block_number", "address", "slot", "from_value", "to_value", "n_diffs"],
        ),
        "balance_reads_agg.parquet": pd.DataFrame(
            [(1, 0, address_a, 1)],
            columns=["block_number", "transaction_index", "address", "read_count"],
        ),
        "nonce_reads_agg.parquet": pd.DataFrame(
            [(1, 1, address_b, 1)],
            columns=["block_number", "transaction_index", "address", "read_count"],
        ),
        "balance_block_mutations.parquet": pd.DataFrame(
            [(1, address_a, "0", "1"), (2, address_a, "1", "2")],
            columns=["block_number", "address", "from_value", "to_value"],
        ),
        "nonce_block_mutations.parquet": pd.DataFrame(
            [(1, address_b, 1, 2)],
            columns=["block_number", "address", "from_value", "to_value"],
        ),
    }
    for filename, table in tables.items():
        table.to_parquet(path / filename, index=False)
    return path


@pytest.fixture(scope="module")
def summary(data_dir):
    return validation_summary(data_dir)


@pytest.fixture(scope="module")
def results(data_dir):
    return build_results_table(data_dir, s_values=range(254))


def test_validation_summary_reconciles(summary):
    for rejected in summary["rejected_counts"].values():
        for v in rejected.values():
            assert isinstance(v, int)
            assert v == 0

    partition = summary["read_partition_check"]
    assert partition["partition_holds"]
    assert partition["n_tx_read"] + partition["n_tx_read_write"] == partition["n_reads"]

    block_partition = summary["block_read_partition_check"]
    assert block_partition["partition_holds"]
    assert (
        block_partition["n_block_read"] + block_partition["n_block_read_write"]
        == block_partition["n_block_reads"]
    )

    weighted = summary["read_count_weighted_partition_check"]
    assert weighted["partition_holds"]

    assert summary["storage_block_mutations_key_unique"]
    assert summary["storage_tx_mutations_key_unique"]
    assert summary["tx_write_keys_all_observed_as_reads"]["holds"]
    assert summary["block_write_keys_all_observed_as_reads"]["holds"]


def test_build_results_table_schema(results):
    assert list(results.columns) == RESULT_COLUMNS
    assert set(results["metric"].unique()) == {
        "event_locality",
        "distinct_leaves",
        "distinct_stems",
        "basic_data_colocation",
        "mutation_kind",
    }


def test_event_locality_fractions_are_in_unit_interval(results):
    subset = results[results["metric"] == "event_locality"]
    assert subset["S"].min() == 0
    assert subset["S"].max() == 253
    valid = subset.dropna(subset=["value"])
    assert (valid["value"] >= 0).all()
    assert (valid["value"] <= 1).all()
    assert (subset["denominator"] >= 0).all()


def test_event_locality_curve_is_monotonic_nondecreasing(results):
    # Fraction of events with slot < S can only grow (or stay flat) as S grows.
    for series in [
        "is_tx_touched",
        "is_block_touched",
        "is_tx_write",
        "is_block_write",
        "is_tx_touched_with_account",
        "is_block_write_with_account",
    ]:
        curve = (
            results[(results["metric"] == "event_locality") & (results["series"] == series)]
            .sort_values("S")["value"]
            .to_numpy()
        )
        assert np.all(np.diff(curve) >= -1e-12), series


def test_event_locality_with_account_series_never_exceeds_pure_series(results):
    # "_with_account" restricts the numerator to a subset of the pure series' touches,
    # over the *same* denominator, so its captured fraction can never exceed the pure
    # curve's at any S.
    base_series = [
        "is_tx_touched",
        "is_block_touched",
        "is_block_write",
    ]
    df = results[results["metric"] == "event_locality"]
    for series in base_series:
        pure = df[df["series"] == series].sort_values("S")
        gated = df[df["series"] == f"{series}_with_account"].sort_values("S")
        assert len(pure) == len(gated)
        merged = pure.merge(gated, on="S", suffixes=("_pure", "_gated"))
        assert (merged["value_gated"] <= merged["value_pure"] + 1e-12).all(), series
        assert np.allclose(merged["denominator_pure"], merged["denominator_gated"]), series
    # is_tx_write has no per-transaction balance/nonce mutation table to gate against.
    assert not (df["series"] == "is_tx_write_with_account").any()


def test_read_only_and_write_keys_are_disjoint(data_dir):
    # is_write_coupled (classify.py) partitions the raw reads table into read-only and
    # write-coupled keys; this is no longer how the published is_tx_touched/is_block_touched
    # series are built (they use the full, unfiltered reads table), but the partition itself
    # is still a real invariant of the classification. This re-derives it directly from the
    # fixture keys (not just the aggregated results table) to confirm zero overlap between
    # read-only keys and write keys, rather than trusting the boolean-mask construction to be
    # bug-free.
    raw = _load_raw(data_dir)
    clean, _ = _normalize_all(raw)
    reads = classify.classify_reads(clean["storage_reads"], clean["storage_tx_mutations"])
    reads_block = classify.classify_reads_block(reads, clean["storage_block_mutations"])

    tx_keys = ["block_number", "transaction_index", "address", "slot"]
    tx_overlap = reads.loc[~reads["is_write_coupled"], tx_keys].merge(
        clean["storage_tx_mutations"][tx_keys].drop_duplicates(), on=tx_keys, how="inner"
    )
    assert tx_overlap.empty

    block_keys = ["block_number", "address", "slot"]
    block_overlap = reads_block.loc[~reads_block["is_write_coupled"], block_keys].merge(
        clean["storage_block_mutations"][block_keys].drop_duplicates(),
        on=block_keys,
        how="inner",
    )
    assert block_overlap.empty


def test_distinct_leaves_are_s_invariant(results):
    subset = results[results["metric"] == "distinct_leaves"]
    for (series, granularity), group in subset.groupby(["series", "granularity"]):
        assert group["value"].nunique() == 1
        assert (group["value"] > 0).all()


def test_distinct_stems_placement_validity(results):
    subset = results[results["metric"] == "distinct_stems"]
    current_anchored = subset[subset["placement"] == "current_anchored"]
    assert current_anchored["S"].max() <= 192
    compact = subset[subset["placement"] == "compact"]
    assert compact["S"].max() == 253
    # Same-S, same-series, same-granularity stem counts must match across placements
    # (placement changes the suffix, never the stem identity/count).
    merged = compact.merge(
        current_anchored,
        on=["series", "granularity", "S"],
        suffixes=("_compact", "_anchored"),
    )
    assert np.allclose(merged["value_compact"], merged["value_anchored"])


def test_distinct_stems_bounded_by_distinct_leaves(results):
    # A stem can hold multiple leaves, so #stems <= #leaves at every S, for every series
    # that has both metrics defined (reads / tx_write_counts / block_write_counts).
    leaves = results[results["metric"] == "distinct_leaves"]
    stems = results[(results["metric"] == "distinct_stems") & (results["placement"] == "compact")]
    for (series, granularity), leaf_group in leaves.groupby(["series", "granularity"]):
        leaf_value = leaf_group["value"].iloc[0]
        stem_group = stems[(stems["series"] == series) & (stems["granularity"] == granularity)]
        assert (stem_group["value"] <= leaf_value + 1e-9).all(), (series, granularity)


def test_basic_data_colocation_fractions_are_in_unit_interval(results):
    subset = results[results["metric"] == "basic_data_colocation"]
    assert set(subset["series"].unique()) == {"read", "write"}
    valid = subset.dropna(subset=["value"])
    assert (valid["value"] >= 0).all()
    assert (valid["value"] <= 1).all()


def test_mutation_kind_rows_present_and_nonnegative(results):
    subset = results[results["metric"] == "mutation_kind"]
    assert (subset["S"] == -1).all()
    assert set(subset["series"].unique()) == {"insertion", "update", "deletion"}
    assert (subset["value"] >= 0).all()
    for granularity in ["transaction", "block"]:
        assert set(subset[subset["granularity"] == granularity]["series"]) == {
            "insertion",
            "update",
            "deletion",
        }


def test_results_written_to_parquet(results, tmp_path):
    out_path = tmp_path / "results.parquet"
    results.to_parquet(out_path, index=False)
    assert out_path.exists()
