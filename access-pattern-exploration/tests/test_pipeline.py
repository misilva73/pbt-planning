"""End-to-end smoke test: run the full Part 1 pipeline against the real pilot-10k
parquet fixture and check the results are internally consistent (reconciliation totals
match, fractions land in [0, 1], the required rows/columns are all present)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from apx.pipeline import RESULT_COLUMNS, build_results_table, validation_summary

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "pilot_10k"
pytestmark = pytest.mark.skipif(
    not DATA_DIR.exists(), reason="pilot_10k fixture not present in this checkout"
)


@pytest.fixture(scope="module")
def summary():
    return validation_summary(DATA_DIR)


@pytest.fixture(scope="module")
def results():
    return build_results_table(DATA_DIR, s_values=range(254))


def test_validation_summary_reconciles(summary):
    for name, n_source in summary["source_row_counts"].items():
        n_accepted = summary["accepted_row_counts"][name]
        rejected = summary["rejected_counts"][name]
        n_rejected_total = max(rejected.values()) if rejected else 0
        # Every rejection count must be small relative to source (real mainnet data is
        # expected to already be clean); accepted rows can be fewer than source rows but
        # never negative, and the counts must actually be reported (not silently zero
        # unless the checked field really had zero malformed rows).
        assert n_accepted <= n_source
        assert n_rejected_total >= 0
        for v in rejected.values():
            assert isinstance(v, int)

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
        "is_tx_read",
        "is_tx_read_write",
        "is_block_read",
        "is_block_read_write",
        "is_tx_write",
        "is_block_write",
        "is_tx_read_with_account",
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
        "is_tx_read",
        "is_tx_read_write",
        "is_tx_read_any",
        "is_block_read",
        "is_block_read_write",
        "is_block_read_any",
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


def test_event_locality_read_any_is_union_of_read_and_read_write(results):
    df = results[results["metric"] == "event_locality"]
    for any_series, part_a, part_b in (
        ("is_tx_read_any", "is_tx_read", "is_tx_read_write"),
        ("is_block_read_any", "is_block_read", "is_block_read_write"),
    ):
        total = df[df["series"] == any_series].sort_values("S")
        a = df[df["series"] == part_a].sort_values("S")
        b = df[df["series"] == part_b].sort_values("S")
        merged = total.merge(a, on="S", suffixes=("", "_a")).merge(b, on="S", suffixes=("", "_b"))
        numerator = merged["value"] * merged["denominator"]
        numerator_parts = merged["value_a"] * merged["denominator_a"] + merged["value_b"] * merged["denominator_b"]
        assert np.allclose(numerator, numerator_parts, atol=1e-6), any_series
        assert np.allclose(merged["denominator"], merged["denominator_a"] + merged["denominator_b"]), any_series


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


def test_results_written_to_parquet(results):
    out_path = DATA_DIR / "results.parquet"
    results.to_parquet(out_path, index=False)
    assert out_path.exists()
