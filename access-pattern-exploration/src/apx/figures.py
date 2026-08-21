"""Seaborn/Matplotlib figure builders for the Part 1 report.

Each function takes the full tidy results table (see apx.pipeline.build_results_table)
and filters internally to the metric it needs, so callers never have to pre-slice the
table. Figures share one color-per-series convention (SERIES_COLORS) and save directly to
PNG via Figure.savefig — no external renderer (Kaleido/Chromium) required.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.figure import Figure
from matplotlib.ticker import PercentFormatter

sns.set_theme(style="whitegrid")

# S values singled out in project-scope.md; the sweep line itself stays unmarked so 254
# points don't clutter the chart, and only these get an extra marker layer.
EMPHASIZED_S = [0, 8, 16, 32, 64, 96, 128, 192, 253]
METADATA_S = 0
CURRENT_S = 64

# The event_locality series, split into the two cost families (project-scope.md):
# touched models witness/proof cost, write models state-root rehash cost. Touched is a
# superset of write, not disjoint from it: is_tx_touched/is_block_touched count every key
# touched at all in that scope, so a write-coupled key is counted in both its touched and
# its write series (see pipeline._event_locality_rows). On the touched side, the
# "_with_account" restriction (same denominator, numerator restricted to touches whose
# account was also BASIC_DATA-accessed in the same scope) never removes anything -- every
# storage access requires a call into that contract, which always resolves the account's
# own header fields too -- so those series are identical to their pure counterpart and are
# not plotted or tabled separately (see the report's Witness cost section). On the write
# side the restriction does bite, so both pure and "_with_account" write series are kept,
# except "is_tx_write", which has no per-transaction balance/nonce mutation table to check
# co-mutation against.
TOUCHED_SERIES = ["is_tx_touched", "is_block_touched"]
WRITE_PURE_SERIES = ["is_tx_write", "is_block_write"]
WRITE_COACCESS_SERIES = ["is_block_write_with_account"]

# One color per series name, stable across every chart that shares a series name
# (e.g. "tx_write_counts" and "block_write_counts" appear in both event_locality and
# the leaf/stem replay).
SERIES_ORDER = [
    *TOUCHED_SERIES,
    *WRITE_PURE_SERIES,
    *WRITE_COACCESS_SERIES,
    "tx_write_counts",
    "block_write_counts",
    "reads",
    "read",
    "write",
]
SERIES_COLORS = dict(zip(SERIES_ORDER, sns.color_palette("tab10", n_colors=len(SERIES_ORDER)).as_hex()))


def _series_order(df: pd.DataFrame) -> list[str]:
    present = set(df["series"].unique())
    return [s for s in SERIES_ORDER if s in present]


def _mark_reference_lines(ax: plt.Axes) -> None:
    label_box = dict(facecolor="white", edgecolor="none", alpha=0.75, pad=1)
    ax.axvline(METADATA_S, linestyle=":", color="gray", linewidth=1)
    ax.axvline(CURRENT_S, linestyle="--", color="gray", linewidth=1)
    # Stacked at different heights (rather than both flush with the top) so the two
    # labels don't collide when S=0 and S=64 fall close together on the x-axis.
    ax.text(
        METADATA_S, 0.98, "metadata-only (S=0)", transform=ax.get_xaxis_transform(),
        ha="left", va="top", fontsize=8, color="gray", bbox=label_box,
    )
    ax.text(
        CURRENT_S, 0.90, "current design (S=64)", transform=ax.get_xaxis_transform(),
        ha="left", va="top", fontsize=8, color="gray", bbox=label_box,
    )


def _locality_panel(ax: plt.Axes, sub: pd.DataFrame, order: list[str], panel_title: str, ylabel: str) -> None:
    if sub.empty:
        ax.set_title(panel_title)
        return
    sns.lineplot(data=sub, x="S", y="value", hue="series", hue_order=order, palette=SERIES_COLORS, ax=ax)
    emphasized = sub[sub["S"].isin(EMPHASIZED_S)]
    sns.scatterplot(
        data=emphasized, x="S", y="value", hue="series", hue_order=order, palette=SERIES_COLORS,
        ax=ax, legend=False, s=45, edgecolor="black", linewidth=0.5, zorder=5,
    )
    _mark_reference_lines(ax)
    ax.set_xlim(left=0)
    ax.yaxis.set_major_formatter(PercentFormatter(xmax=1.0))
    ax.set_xlabel("header window size (S)")
    ax.set_ylabel(ylabel)
    ax.set_title(panel_title)
    ax.legend(title="", bbox_to_anchor=(1.02, 1), loc="upper left", frameon=False, fontsize=8)


def _plot_single_cost_locality(results: pd.DataFrame, series: list[str], panel_title: str, fig_title: str) -> Figure:
    """One-panel plot for a single cost-family series group, S-swept."""
    df = results[results["metric"] == "event_locality"].sort_values("S")
    sub = df[df["series"].isin(series)]
    fig, ax = plt.subplots(figsize=(8, 5))
    order = [s for s in series if s in set(sub["series"].unique())]
    _locality_panel(ax, sub, order, panel_title, "captured fraction")
    fig.suptitle(fig_title)
    fig.tight_layout()
    return fig


def plot_witness_cost_touched(results: pd.DataFrame) -> Figure:
    """Touched-side event-locality series (witness/proof cost), pure occurrence only --
    the account-co-accessed counterpart is identical for every touched series, see the
    TOUCHED_SERIES module comment."""
    return _plot_single_cost_locality(
        results, TOUCHED_SERIES, "pure occurrence",
        "Witness cost (touched): captured fraction by header window size",
    )


def plot_state_root_cost_writes_pure(results: pd.DataFrame) -> Figure:
    """Write-side event-locality series (state-root rehash cost): every net-changed key,
    regardless of whether its account was independently BASIC_DATA-mutated."""
    return _plot_single_cost_locality(
        results, WRITE_PURE_SERIES, "pure occurrence",
        "State-root cost (writes): pure occurrence by header window size",
    )


def plot_state_root_cost_writes_coaccess(results: pd.DataFrame) -> Figure:
    """Write-side event-locality series restricted to keys whose account was also
    BASIC_DATA-mutated in the same block -- same denominator as the pure curve. "is_tx_write"
    has no such counterpart -- see WRITE_COACCESS_SERIES module comment."""
    return _plot_single_cost_locality(
        results, WRITE_COACCESS_SERIES, "co-accessed with account",
        "State-root cost (writes): co-accessed with account by header window size",
    )


def plot_leaf_stem_replay(results: pd.DataFrame, granularity: str) -> Figure:
    """Distinct stem count (varies with S and placement) against distinct leaf count
    (flat, invariant to S) for one granularity, faceted by placement."""
    stems = results[
        (results["metric"] == "distinct_stems") & (results["granularity"] == granularity)
    ].copy()
    leaves = results[
        (results["metric"] == "distinct_leaves") & (results["granularity"] == granularity)
    ].copy()

    stems["kind"] = "stems"
    placements = sorted(stems["placement"].unique().tolist()) or ["n/a"]
    leaves_expanded = pd.concat(
        [leaves.assign(placement=p, kind="leaves") for p in placements], ignore_index=True
    )

    cols = ["series", "S", "value", "placement", "kind"]
    combined = pd.concat([stems[cols], leaves_expanded[cols]], ignore_index=True)
    order = _series_order(combined)

    fig, axes = plt.subplots(1, len(placements), figsize=(5.5 * len(placements), 5), sharey=True, squeeze=False)
    axes = axes[0]
    for ax, placement in zip(axes, placements):
        sub = combined[combined["placement"] == placement]
        sns.lineplot(
            data=sub, x="S", y="value", hue="series", hue_order=order, style="kind",
            style_order=["stems", "leaves"], palette=SERIES_COLORS, ax=ax,
            legend="full" if ax is axes[-1] else False,
        )
        ax.set_title(placement)
        ax.set_xlabel("header window size (S)")
        ax.set_ylabel("distinct count" if ax is axes[0] else "")
    axes[-1].legend(title="", bbox_to_anchor=(1.02, 1), loc="upper left", frameon=False)
    fig.suptitle(f"Distinct leaves vs. stems ({granularity} granularity)")
    fig.tight_layout()
    return fig
