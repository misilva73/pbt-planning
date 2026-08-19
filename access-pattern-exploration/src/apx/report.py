"""Assemble the Part 1 markdown report from the tidy results table.

Writes each figure as a PNG under out_dir/figures/, embedded inline in report.md via
standard markdown image syntax so it renders in any viewer (VS Code preview, GitHub, a
PDF export) with no extra step. report.md's section order follows project-scope.md:
methodology, data-quality notes, event-locality curves, leaf/stem replay, basic_data
co-location, mutation-kind diagnostics, S=0/S=64 comparison, limitations.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd

from apx.figures import (
    CURRENT_S,
    METADATA_S,
    READ_COACCESS_SERIES,
    READ_PURE_SERIES,
    SERIES_ORDER,
    WRITE_COACCESS_SERIES,
    WRITE_PURE_SERIES,
    plot_basic_data_colocation,
    plot_leaf_stem_replay,
    plot_mutation_kind,
    plot_state_root_cost_writes,
    plot_witness_cost_reads,
)

FIGURES_DIR_NAME = "figures"

# Definitions for the event_locality series, per classify.classify_reads(_block) and
# pipeline._event_locality_rows. Reads model witness/proof cost, writes model
# state-root rehash cost; both are occurrence counts (one row per distinct key touched,
# never weighted by touch count). Each pure series has a "_with_account" counterpart:
# same denominator, numerator restricted to touches whose account was also BASIC_DATA-
# accessed in the same scope -- the only touches where the header window's stem-sharing
# can actually pay off. "is_tx_write" has no such counterpart (see its description).
EVENT_SERIES_DESCRIPTIONS = {
    "is_tx_read": (
        "Distinct (block, transaction, address, slot) keys read but never written in "
        "that transaction: one row per occurrence, regardless of how many times the "
        "slot was read."
    ),
    "is_tx_read_write": (
        "Distinct (block, transaction, address, slot) keys read and also written "
        "(net-changed) in that same transaction: one row per occurrence, regardless of "
        "how many times the slot was read."
    ),
    "is_tx_read_any": (
        "Distinct (block, transaction, address, slot) keys read in that transaction, "
        "whether or not they were also written: the union of `is_tx_read` and "
        "`is_tx_read_write`."
    ),
    "is_block_read": (
        "Distinct (block, address, slot) keys read by at least one transaction in the "
        "block but never net-changed in that block."
    ),
    "is_block_read_write": (
        "Distinct (block, address, slot) keys read by at least one transaction in the "
        "block and also net-changed in that block."
    ),
    "is_block_read_any": (
        "Distinct (block, address, slot) keys read by at least one transaction in the "
        "block, whether or not they were also net-changed: the union of "
        "`is_block_read` and `is_block_read_write`."
    ),
    "is_tx_write": (
        "Per-transaction storage mutations: one row per (block, transaction, address, "
        "slot) whose value changed within that transaction (no-ops already excluded)."
    ),
    "is_block_write": (
        "Block-final net storage mutations: one row per (block, address, slot) whose "
        "value changed net across the whole block (no-ops already excluded)."
    ),
    "is_tx_read_with_account": (
        "`is_tx_read` restricted to keys whose account also had an observed "
        "balance/nonce read in the same transaction (the BASIC_DATA read proxy) -- the "
        "only touches where sharing the account's header stem can actually save a "
        "witness lookup. Same denominator as `is_tx_read`."
    ),
    "is_tx_read_write_with_account": (
        "`is_tx_read_write` restricted the same way: keys whose account also had an "
        "observed balance/nonce read in the same transaction. Same denominator as "
        "`is_tx_read_write`."
    ),
    "is_tx_read_any_with_account": (
        "`is_tx_read_any` restricted the same way: keys whose account also had an "
        "observed balance/nonce read in the same transaction. Same denominator as "
        "`is_tx_read_any`."
    ),
    "is_block_read_with_account": (
        "`is_block_read` restricted to keys whose account also had an observed "
        "balance/nonce read anywhere in the block. Same denominator as `is_block_read`."
    ),
    "is_block_read_write_with_account": (
        "`is_block_read_write` restricted the same way: keys whose account also had an "
        "observed balance/nonce read anywhere in the block. Same denominator as "
        "`is_block_read_write`."
    ),
    "is_block_read_any_with_account": (
        "`is_block_read_any` restricted the same way: keys whose account also had an "
        "observed balance/nonce read anywhere in the block. Same denominator as "
        "`is_block_read_any`."
    ),
    "is_block_write_with_account": (
        "`is_block_write` restricted to keys whose account also had an observed "
        "balance/nonce mutation in the same block (the BASIC_DATA mutation proxy) -- "
        "the only touches where sharing the account's header stem can actually save a "
        "state-root rehash. Same denominator as `is_block_write`. `is_tx_write` has no "
        "such counterpart: no per-transaction balance/nonce mutation table is "
        "extracted, so per-transaction co-mutation can't be checked without "
        "overstating it via this block-level proxy."
    ),
}


def _write_figures(results: pd.DataFrame, fig_dir: Path) -> dict[str, str]:
    """Write each figure as a PNG and return {stem: relpath} for the markdown sections
    to reference."""
    fig_dir.mkdir(parents=True, exist_ok=True)
    figures = {
        "witness_cost_reads": plot_witness_cost_reads(results),
        "state_root_cost_writes": plot_state_root_cost_writes(results),
        "leaf_stem_transaction": plot_leaf_stem_replay(results, "transaction"),
        "leaf_stem_block": plot_leaf_stem_replay(results, "block"),
        "basic_data_colocation": plot_basic_data_colocation(results),
        "mutation_kind": plot_mutation_kind(results),
    }
    paths: dict[str, str] = {}
    for stem, fig in figures.items():
        fig.savefig(fig_dir / f"{stem}.png", dpi=150)
        plt.close(fig)
        paths[stem] = f"{FIGURES_DIR_NAME}/{stem}.png"
    return paths


def _figure_markdown(paths: dict[str, str], stem: str, alt: str) -> str:
    return f"![{alt}]({paths[stem]})"


def _ordered_series(df: pd.DataFrame) -> list[str]:
    present = set(df["series"].unique())
    ordered = [s for s in SERIES_ORDER if s in present]
    return ordered + sorted(present - set(ordered))


def _fmt(value: float | None, as_percent: bool) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "n/a"
    return f"{value:.1%}" if as_percent else f"{value:,.0f}"


def _value_at(df: pd.DataFrame, series: str, s: int, granularity: str | None = None) -> float | None:
    mask = (df["series"] == series) & (df["S"] == s)
    if granularity is not None:
        mask &= df["granularity"] == granularity
    sub = df[mask]
    return float(sub["value"].iloc[0]) if not sub.empty else None


def _markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join(lines)


def _dict_to_table(d: dict[str, Any]) -> str:
    rows = []
    for key, value in d.items():
        if isinstance(value, list):
            rendered = "; ".join(str(v) for v in value)
        elif isinstance(value, dict):
            rendered = "; ".join(f"{k}={v}" for k, v in value.items())
        else:
            rendered = str(value)
        rows.append([key, rendered])
    return _markdown_table(["Check", "Result"], rows)


def _methodology_section(results: pd.DataFrame) -> str:
    df = results[results["metric"] == "event_locality"]
    summary_table = _event_series_summary_table(df)
    return (
        "## Methodology summary\n\n"
        "Part 1 sweeps the header storage window `S` from 0 to 253 with `C=0`, emphasizing "
        "`S in {0, 8, 16, 32, 64, 96, 128, 192, 253}`. `S=0` is the metadata-only baseline "
        "and `S=64` matches the current `HEADER_STORAGE_SLOTS` design. For each `S`, a "
        "storage slot `x` is in the header if `x < S`. Two suffix placements are evaluated: "
        "compact (`suffix = 3 + x`, valid for every `S`) and current-anchored "
        "(`suffix = 64 + x`, valid only up to `S=192`, matching the live layout exactly at "
        "`S=64`). This report tracks two cost dimensions, each an occurrence count (one "
        "row per distinct key touched, never weighted by how many times it was touched "
        "-- see the Limitations section for why): witness/proof cost for reads "
        "(`is_tx_read*` / `is_block_read*`) and state-root rehash cost for writes "
        "(`is_tx_write` / `is_block_write`). Each series has a `_with_account` "
        "counterpart sharing the same denominator, restricted to touches whose account "
        "was also BASIC_DATA-accessed in the same scope -- the header window's "
        "stem-sharing only pays off when a slot's stem would otherwise need touching "
        "anyway for the account's own header fields. All counts in this report are "
        "Tier 1: exact event, distinct-leaf, "
        "and distinct-stem counts from canonical access data. Tier 2 metrics (proof "
        "siblings, witness bytes, recomputed hashes) require a pinned PBT implementation "
        "and pre-state and are out of scope for this deliverable.\n\n"
        "### Event series summary\n\n"
        "Total event count per series, independent of `S` (the denominator behind "
        f"every captured-fraction figure below).\n\n{summary_table}"
    )


def _data_quality_section(validation: dict[str, Any]) -> str:
    if not validation:
        body = "No reconciliation data was supplied."
    else:
        body = _dict_to_table(validation)
    return "## Data quality and reconciliation\n\n" + body


def _event_series_summary_table(df: pd.DataFrame) -> str:
    """Total event count and definition per series (the total is S-invariant: the
    denominator behind every captured-fraction row for that series), so the percentages
    below have an absolute scale and a definition to be read against."""
    rows = []
    for series in _ordered_series(df):
        sub = df[df["series"] == series]
        total = float(sub["denominator"].iloc[0]) if not sub.empty else None
        description = EVENT_SERIES_DESCRIPTIONS.get(series, "n/a")
        rows.append([series, description, _fmt(total, False)])
    return _markdown_table(["Series", "Description", "Total events"], rows)


def _cost_locality_table(results: pd.DataFrame, series_names: list[str]) -> str:
    df = results[(results["metric"] == "event_locality") & (results["series"].isin(series_names))]
    rows = []
    for series in _ordered_series(df):
        sub = df[df["series"] == series]
        rows.append(
            [
                series,
                _fmt(_value_at(sub, series, METADATA_S), True),
                _fmt(_value_at(sub, series, CURRENT_S), True),
                _fmt(_value_at(sub, series, 253), True),
            ]
        )
    return _markdown_table(["Series", "S=0", "S=64", "S=253"], rows)


def _witness_cost_section(results: pd.DataFrame, fig_paths: dict[str, str]) -> str:
    table = _cost_locality_table(results, READ_PURE_SERIES + READ_COACCESS_SERIES)
    figure = _figure_markdown(fig_paths, "witness_cost_reads", "Witness cost (reads) by header window size")
    return (
        "## Witness cost (reads)\n\n"
        "Captured fraction of each read-side occurrence series for a header window of "
        "size `S`. The left panel is the raw occurrence curve (every distinct key "
        "touched, transaction- or block-grain); the right panel restricts the "
        "numerator to touches whose account was also BASIC_DATA-accessed in the same "
        "scope, over the *same* denominator -- the only touches where being inside the "
        "header window can actually shrink a witness, since a slot's stem needs "
        "proving either way once something else in it is independently needed.\n\n"
        f"{figure}\n\n{table}"
    )


def _state_root_cost_section(results: pd.DataFrame, fig_paths: dict[str, str]) -> str:
    table = _cost_locality_table(results, WRITE_PURE_SERIES + WRITE_COACCESS_SERIES)
    figure = _figure_markdown(fig_paths, "state_root_cost_writes", "State-root cost (writes) by header window size")
    return (
        "## State-root cost (writes)\n\n"
        "Captured fraction of each write-side occurrence series for a header window of "
        "size `S`. The left panel is the raw net-mutation occurrence curve; the right "
        "panel restricts the numerator to keys whose account was also BASIC_DATA-"
        "mutated in the same block, over the *same* denominator -- the only mutations "
        "where sharing the header stem actually saves a rehash, since the stem needs "
        "rehashing either way once something else inside it changed. `is_tx_write` has "
        "no account-restricted counterpart (see Limitations).\n\n"
        f"{figure}\n\n{table}"
    )


def _leaf_stem_section(results: pd.DataFrame, fig_paths: dict[str, str]) -> str:
    tx_figure = _figure_markdown(fig_paths, "leaf_stem_transaction", "Distinct leaves vs stems, per transaction")
    block_figure = _figure_markdown(fig_paths, "leaf_stem_block", "Distinct leaves vs stems, per block")
    return (
        "## Distinct leaf and stem replay\n\n"
        "Distinct leaf counts are invariant to `S`: moving a slot into the header changes "
        "its key, not whether it was touched. Distinct stem counts fall as `S` grows, "
        "because more slots collapse into shared header stems. Both placements (compact, "
        f"current-anchored) are shown; current-anchored is only defined up to `S=192`.\n\n"
        f"{tx_figure}\n\n{block_figure}"
    )


def _basic_data_section(results: pd.DataFrame, fig_paths: dict[str, str]) -> str:
    df = results[results["metric"] == "basic_data_colocation"]
    rows = []
    for series in _ordered_series(df):
        sub = df[df["series"] == series]
        rows.append(
            [
                series,
                _fmt(_value_at(sub, series, METADATA_S), True),
                _fmt(_value_at(sub, series, CURRENT_S), True),
                _fmt(_value_at(sub, series, 253), True),
            ]
        )
    table = _markdown_table(["Series", "S=0", "S=64", "S=253"], rows)
    figure = _figure_markdown(fig_paths, "basic_data_colocation", "BASIC_DATA co-location fraction")
    return (
        "## BASIC_DATA co-location\n\n"
        "How often a low-index storage access shares an account header stem with an "
        "observed `BASIC_DATA` access or mutation. This is an observed-metadata lower "
        f"bound: it excludes code-hash resolution and other implied header reads.\n\n"
        f"{figure}\n\n{table}"
    )


def _mutation_kind_section(results: pd.DataFrame, fig_paths: dict[str, str]) -> str:
    df = results[results["metric"] == "mutation_kind"]
    rows = []
    for series in _ordered_series(df):
        sub = df[df["series"] == series]
        block_value = _value_at(sub, series, -1, granularity="block")
        tx_value = _value_at(sub, series, -1, granularity="transaction")
        rows.append([series, _fmt(block_value, False), _fmt(tx_value, False)])
    table = _markdown_table(["Kind", "Block-final count", "Transaction-sensitivity count"], rows)
    figure = _figure_markdown(fig_paths, "mutation_kind", "Mutation-kind breakdown")
    return (
        "## Mutation-kind diagnostics\n\n"
        "Zero-to-nonzero (insertion), nonzero-to-nonzero (update), and nonzero-to-zero "
        "(deletion) mutations, counted separately. Their union is the net-mutation "
        f"denominator used elsewhere in this report.\n\n{figure}\n\n{table}"
    )


def _comparison_section(results: pd.DataFrame) -> str:
    event_df = results[results["metric"] == "event_locality"]
    rows = []
    for series in _ordered_series(event_df):
        sub = event_df[event_df["series"] == series]
        s0 = _value_at(sub, series, METADATA_S)
        s64 = _value_at(sub, series, CURRENT_S)
        delta = None if s0 is None or s64 is None else s64 - s0
        rows.append(
            [
                series,
                _fmt(s0, True),
                _fmt(s64, True),
                _fmt(delta, True) if delta is not None else "n/a",
            ]
        )
    table = _markdown_table(["Series", "Metadata-only (S=0)", "Current (S=64)", "Gain"], rows)
    return (
        "## Comparison against S=0 and current S=64\n\n"
        "The gain column is the captured-fraction increase the current 64-slot window "
        "buys over the metadata-only baseline, for each event-locality series.\n\n" + table
    )


def _limitations_section() -> str:
    return (
        "## Limitations\n\n"
        "1. This report reflects backward-looking mainnet behavior shaped by MPT-era gas "
        "costs; it describes how well the current window serves current behavior, not how "
        "contracts would relayout under PBT's own repricing.\n"
        "2. The read channel estimates proof and witness work. Stateful clients may serve "
        "ordinary execution reads from flat state, so these curves should not be read as a "
        "claim about flat-state lookup latency.\n"
        "3. Only Tier 1 metrics are reported. Exact proof siblings, witness bytes, and "
        "recomputed hashes require a pinned PBT implementation and pre-state and remain "
        "deferred.\n"
        "4. The sampled block range skews toward whatever contracts were active during it "
        "and should not be read as representative of all Ethereum contracts.\n"
        "5. The `BASIC_DATA` co-location proxy is an observed lower bound built from "
        "balance and nonce reads and diffs; it excludes code-hash resolution and other "
        "implied header reads.\n"
        "6. All event_locality series are occurrence counts, not weighted by how many "
        "times a key was touched: witness cost is paid once per distinct key a block's "
        "execution needs proved, and state-root rehash cost is paid once per distinct "
        "key net-changed, in each case regardless of raw touch multiplicity (further, "
        "even EVM gas accounting already dedupes to first-touch-per-transaction via "
        "EIP-2929 warm/cold pricing).\n"
        "7. `is_tx_write` has no `_with_account` counterpart: only block-final "
        "balance/nonce mutations are extracted (no per-transaction table), so "
        "per-transaction account co-mutation can't be checked without overstating it "
        "via the block-level proxy."
    )


def build_report(results: pd.DataFrame, validation: dict[str, Any], out_dir: Path) -> Path:
    """Write figures and report.md under out_dir and return the report path."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_paths = _write_figures(results, out_dir / FIGURES_DIR_NAME)

    sections = [
        "# Part 1: Storage-Window Locality and Stem Replay",
        _methodology_section(results),
        _witness_cost_section(results, fig_paths),
        _state_root_cost_section(results, fig_paths),
        _leaf_stem_section(results, fig_paths),
        _basic_data_section(results, fig_paths),
        _mutation_kind_section(results, fig_paths),
        _comparison_section(results),
        _limitations_section(),
        _data_quality_section(validation),
    ]
    report_path = out_dir / "report.md"
    report_path.write_text("\n\n".join(sections) + "\n")
    return report_path
