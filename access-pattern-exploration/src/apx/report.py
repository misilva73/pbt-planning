"""Assemble the Part 1 markdown report from the tidy results table.

Writes each figure as a PNG under out_dir/figures/, embedded inline in report.md via
standard markdown image syntax so it renders in any viewer (VS Code preview, GitHub, a
PDF export) with no extra step. report.md's section order follows project-scope.md:
methodology, witness cost (touched), state-root cost (writes, including the BASIC_DATA
co-location table), leaf/stem replay, limitations, data-quality notes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd

from apx.figures import (
    CURRENT_S,
    METADATA_S,
    SERIES_ORDER,
    TOUCHED_SERIES,
    WRITE_COACCESS_SERIES,
    WRITE_PURE_SERIES,
    plot_leaf_stem_replay,
    plot_state_root_cost_writes_coaccess,
    plot_state_root_cost_writes_pure,
    plot_witness_cost_touched,
)

FIGURES_DIR_NAME = "figures"

# Series that are the same population by definition, and therefore share the same total
# (the "denominator" column): a "_with_account" restriction shares its base series'
# denominator by construction (same population, narrower numerator) rather than having its
# own -- see figures.py's TOUCHED_SERIES module comment. Merging these avoids listing
# the same number twice.
EVENT_SERIES_TOTAL_GROUPS = [
    ["is_tx_touched"],
    ["is_block_touched"],
    ["is_tx_write"],
    ["is_block_write", "is_block_write_with_account"],
]


def _write_figures(results: pd.DataFrame, fig_dir: Path) -> dict[str, str]:
    """Write each figure as a PNG and return {stem: relpath} for the markdown sections
    to reference."""
    fig_dir.mkdir(parents=True, exist_ok=True)
    figures = {
        "witness_cost_touched": plot_witness_cost_touched(results),
        "state_root_cost_writes_pure": plot_state_root_cost_writes_pure(results),
        "state_root_cost_writes_coaccess": plot_state_root_cost_writes_coaccess(results),
        "leaf_stem_transaction": plot_leaf_stem_replay(results, "transaction"),
        "leaf_stem_block": plot_leaf_stem_replay(results, "block"),
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


def _event_series_summary_table(df: pd.DataFrame) -> str:
    """One row per group of series that share a total by definition (see
    EVENT_SERIES_TOTAL_GROUPS): the total is the denominator behind every
    captured-fraction figure for that group's series."""
    present = set(df["series"].unique())
    rows = []
    for group in EVENT_SERIES_TOTAL_GROUPS:
        members = [s for s in group if s in present]
        if not members:
            continue
        sub = df[df["series"] == members[0]]
        total = float(sub["denominator"].iloc[0]) if not sub.empty else None
        rows.append([" / ".join(f"`{s}`" for s in members), _fmt(total, False)])
    return _markdown_table(["Series", "Total events"], rows)


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
        "-- see the Limitations section for why): witness/proof cost for every touch "
        "(`is_tx_touched*` / `is_block_touched*`) and state-root rehash cost for writes "
        "(`is_tx_write` / `is_block_write`). All counts in this report are Tier 1: exact "
        "event, distinct-leaf, and distinct-stem counts from canonical access data. Tier 2 "
        "metrics (proof siblings, witness bytes, recomputed hashes) require a pinned PBT "
        "implementation and pre-state and are out of scope for this deliverable.\n\n"
        "### Event series summary\n\n"
        "Two access kinds are tracked per scope: `*_touched` (every key touched at all, "
        "whether or not it was also net-changed) and `*_write` (a key net-changed). "
        "Touched is a superset of write, not disjoint from it: a write-coupled key is "
        "counted in both, since it needs a witness/proof and a rehash on the same event. "
        "Touched models witness/proof cost; write models state-root rehash cost. Each "
        "kind is measured at two grains: `is_tx_*` counts distinct (block, transaction, "
        "address, slot) keys, `is_block_*` counts distinct (block, address, slot) keys "
        "net across the whole block.\n\n"
        "Every series except `is_tx_write` also has a `_with_account` counterpart: the "
        "same population, restricted to touches whose account was also independently "
        "`BASIC_DATA`-accessed or mutated in the same scope -- the only touches where "
        "sharing the header stem can actually save a proof lookup or a rehash. "
        "`is_tx_write` has no such variant because only block-final balance/nonce "
        "mutations are extracted, not per-transaction ones (see Limitations). On the "
        "touched side the restriction never removes anything -- every storage access "
        "already requires resolving the account's own header fields -- so `_with_account` "
        "touched series are identical to their pure counterpart and are omitted below "
        "(see Witness cost (touched)); `is_block_write` and `is_block_write_with_account` "
        "share a denominator by construction and are merged into one row.\n\n"
        "The table below gives each series' total, the denominator behind every "
        f"captured-fraction figure in this report.\n\n{summary_table}"
    )


def _data_quality_section(validation: dict[str, Any]) -> str:
    if not validation:
        body = "No reconciliation data was supplied."
    else:
        body = _dict_to_table(validation)
    return "## Data quality and reconciliation\n\n" + body


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


def _basic_data_colocation_table(results: pd.DataFrame) -> str:
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
    return _markdown_table(["Series", "S=0", "S=64", "S=253"], rows)


def _witness_cost_section(results: pd.DataFrame, fig_paths: dict[str, str]) -> str:
    figure = _figure_markdown(fig_paths, "witness_cost_touched", "Witness cost (touched) by header window size")
    table = _cost_locality_table(results, TOUCHED_SERIES)
    return (
        "## Witness cost (touched)\n\n"
        "This section estimates witness/proof-cost savings from growing the header "
        "storage window `S`: how large a share of all storage touches -- read-only or "
        "later net-changed -- could be proved from the account's already-shared header "
        "stem instead of an independent one, at each window size. A witness has to prove "
        "a key's pre-state value regardless of whether it then gets written, so this "
        "section deliberately covers every touch. It addresses the core sizing question "
        "-- how much locality benefit each additional header slot buys -- separately for "
        "touches counted per transaction and per block. `is_tx_touched` and "
        "`is_block_touched` include any key that was also net-changed in that scope (see "
        "Event series summary), so a write-coupled key contributes to both this section "
        "and State-root cost (writes) -- intentionally, since it incurs both costs on "
        "the same event.\n\n"
        "The plot shows the captured fraction of each touched occurrence series as `S` "
        "grows, one line per series; markers highlight the emphasized `S` values, and the "
        "vertical lines mark the metadata-only (`S=0`) and current (`S=64`) "
        f"designs.\n\n{figure}\n\n"
        "The table gives the same captured fraction at the metadata-only, current, and "
        f"largest swept window sizes, for reference.\n\n{table}\n\n"
        "Every touched series' `_with_account` counterpart (restricted to touches whose "
        "account was also independently `BASIC_DATA`-accessed) is numerically identical "
        "to the pure occurrence series shown here, at every `S` -- see the `read` row of "
        "the BASIC_DATA co-location table in State-root cost (writes), which is 100% "
        "throughout. This report therefore omits `_with_account` touched series. See "
        "Limitations for a caveat on what \"touched\" means given how the underlying data "
        "is collected."
    )


def _state_root_cost_section(results: pd.DataFrame, fig_paths: dict[str, str]) -> str:
    pure_figure = _figure_markdown(
        fig_paths, "state_root_cost_writes_pure", "State-root cost (writes), pure occurrence, by header window size"
    )
    coaccess_figure = _figure_markdown(
        fig_paths, "state_root_cost_writes_coaccess",
        "State-root cost (writes), co-accessed with account, by header window size",
    )
    table = _cost_locality_table(results, WRITE_PURE_SERIES + WRITE_COACCESS_SERIES)
    colocation_table = _basic_data_colocation_table(results)
    return (
        "## State-root cost (writes)\n\n"
        "This section estimates state-root rehash savings from growing `S`: how large a "
        "share of write-side storage mutations could share a stem rehash with the "
        "account's own header fields, at each window size. Unlike reads, whether a "
        "mutation's account was independently `BASIC_DATA`-mutated in the same block "
        "matters here, so pure occurrence and account-co-accessed captured fractions are "
        "shown as two separate plots.\n\n"
        "The first plot is the raw net-mutation occurrence curve: every distinct key "
        "net-changed, regardless of whether its account was independently mutated.\n\n"
        f"{pure_figure}\n\n"
        "The second plot restricts the numerator to keys whose account was also "
        "`BASIC_DATA`-mutated in the same block, over the *same* denominator -- the only "
        "mutations where sharing the header stem actually saves a rehash, since the stem "
        "needs rehashing either way once something else inside it changed. `is_tx_write` "
        "has no such counterpart (see Limitations).\n\n"
        f"{coaccess_figure}\n\n"
        "The table gives the captured fraction of both curves at the metadata-only, "
        f"current, and largest swept window sizes, for reference.\n\n{table}\n\n"
        "The table below shows how often a low-index storage touch shares an account "
        "header stem with an independently observed `BASIC_DATA` access or mutation, by "
        "`S`. The `read` row is the basis for the touched-side note in Witness cost "
        "(touched): it is 100%, confirming that every storage touch's account is "
        "independently accessed. The `write` row is far lower, which is why the "
        "co-accessed curve above "
        "differs materially from the pure occurrence curve. This is an observed-metadata "
        "lower bound: it excludes code-hash resolution and other implied header "
        f"reads.\n\n{colocation_table}"
    )


def _leaf_stem_section(results: pd.DataFrame, fig_paths: dict[str, str]) -> str:
    tx_figure = _figure_markdown(fig_paths, "leaf_stem_transaction", "Distinct leaves vs stems, per transaction")
    block_figure = _figure_markdown(fig_paths, "leaf_stem_block", "Distinct leaves vs stems, per block")
    return (
        "## Distinct leaf and stem replay\n\n"
        "This section checks distinct-key replay: whether shrinking the number of "
        "distinct stems that need proving or rehashing (by moving slots into a shared "
        "header stem) reduces work independently of the occurrence curves above. "
        "Distinct leaf counts are invariant to `S` by construction -- moving a slot into "
        "the header changes its key, not whether it was touched -- while distinct stem "
        "counts fall as `S` grows, because more slots collapse into shared header stems. "
        "Both suffix placements (compact, current-anchored) are shown; current-anchored "
        "is only defined up to `S=192`.\n\n"
        "The first plot is per-transaction distinct leaf and stem counts, faceted by "
        f"placement.\n\n{tx_figure}\n\n"
        "The second plot is the same, per block.\n\n"
        f"{block_figure}"
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
        "via the block-level proxy.\n"
        "8. `canonical_execution_storage_reads` is collected via geth's prestate tracer "
        "(through cryo), which fires its SLOAD/SSTORE hook for both opcodes identically -- "
        "there is no field distinguishing which opcode produced a row. This doesn't "
        "affect `is_tx_touched` / `is_block_touched` themselves, which count every touch "
        "regardless of which opcode produced it; it only means these series can't be "
        "split into \"real `SLOAD`s\" versus SSTORE-implied pre-reads, since the data "
        "doesn't separate them. `is_tx_write` / `is_block_write` are unaffected: they "
        "come from a separate state-diff trace and only include keys with a genuine "
        "value change."
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
        _limitations_section(),
        _data_quality_section(validation),
    ]
    report_path = out_dir / "report.md"
    report_path.write_text("\n\n".join(sections) + "\n")
    return report_path
