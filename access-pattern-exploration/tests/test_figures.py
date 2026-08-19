from __future__ import annotations

from matplotlib.figure import Figure

from apx.figures import (
    EMPHASIZED_S,
    READ_COACCESS_SERIES,
    READ_PURE_SERIES,
    WRITE_COACCESS_SERIES,
    WRITE_PURE_SERIES,
    plot_basic_data_colocation,
    plot_leaf_stem_replay,
    plot_mutation_kind,
    plot_state_root_cost_writes,
    plot_witness_cost_reads,
)
from tests.fixtures import synthetic_results_table


def _data_lines(ax, min_points=3):
    """Real plotted lines, excluding zero-length legend-proxy artists."""
    return [line for line in ax.lines if len(line.get_xdata()) >= min_points]


def _vlines(ax):
    """axvline() artists: constant x, y spanning the full axes (0, 1)."""
    return [line for line in ax.lines if list(line.get_ydata()) == [0, 1]]


def test_plot_witness_cost_reads_has_pure_and_coaccess_panels():
    results = synthetic_results_table()
    fig = plot_witness_cost_reads(results)
    assert isinstance(fig, Figure)
    assert len(fig.axes) == 2
    pure_ax, coaccess_ax = fig.axes

    assert len(_data_lines(pure_ax)) == len(READ_PURE_SERIES)
    assert len(_data_lines(coaccess_ax)) == len(READ_COACCESS_SERIES)

    _, pure_labels = pure_ax.get_legend_handles_labels()
    assert set(pure_labels) == set(READ_PURE_SERIES)
    _, coaccess_labels = coaccess_ax.get_legend_handles_labels()
    assert set(coaccess_labels) == set(READ_COACCESS_SERIES)

    # emphasized S values get an extra marker layer: one point per series per S
    assert max(len(c.get_offsets()) for c in pure_ax.collections) == len(EMPHASIZED_S) * len(READ_PURE_SERIES)

    # current design (S=64) and metadata-only (S=0) should be marked as vertical lines
    assert sorted(line.get_xdata()[0] for line in _vlines(pure_ax)) == [0, 64]


def test_plot_state_root_cost_writes_has_pure_and_coaccess_panels():
    results = synthetic_results_table()
    fig = plot_state_root_cost_writes(results)
    assert isinstance(fig, Figure)
    assert len(fig.axes) == 2
    pure_ax, coaccess_ax = fig.axes

    assert len(_data_lines(pure_ax)) == len(WRITE_PURE_SERIES)
    assert len(_data_lines(coaccess_ax)) == len(WRITE_COACCESS_SERIES)

    _, pure_labels = pure_ax.get_legend_handles_labels()
    assert set(pure_labels) == set(WRITE_PURE_SERIES)
    _, coaccess_labels = coaccess_ax.get_legend_handles_labels()
    assert set(coaccess_labels) == set(WRITE_COACCESS_SERIES)


def test_plot_leaf_stem_replay_facets_by_placement():
    results = synthetic_results_table()
    for granularity in ("transaction", "block"):
        fig = plot_leaf_stem_replay(results, granularity)
        assert isinstance(fig, Figure)
        # two placements (compact, current_anchored) as facet subplots
        assert len(fig.axes) == 2
        assert {ax.get_title() for ax in fig.axes} == {"compact", "current_anchored"}
        for ax in fig.axes:
            assert _data_lines(ax)


def test_plot_leaf_stem_replay_leaf_values_are_flat():
    results = synthetic_results_table()
    fig = plot_leaf_stem_replay(results, "transaction")
    # leaves are style-mapped to a dashed line, stems to solid
    leaf_lines = [line for ax in fig.axes for line in _data_lines(ax) if line.get_linestyle() == "--"]
    assert leaf_lines
    for line in leaf_lines:
        assert len(set(line.get_ydata())) == 1  # flat reference line


def test_plot_basic_data_colocation_has_read_and_write_lines():
    results = synthetic_results_table()
    fig = plot_basic_data_colocation(results)
    assert isinstance(fig, Figure)
    _, labels = fig.axes[0].get_legend_handles_labels()
    assert set(labels) == {"read", "write"}


def test_plot_mutation_kind_is_bar_chart_with_three_kinds():
    results = synthetic_results_table()
    fig = plot_mutation_kind(results)
    assert isinstance(fig, Figure)
    assert len(fig.axes) > 0
    for ax in fig.axes:
        assert len(ax.patches) == 3
        assert {t.get_text() for t in ax.get_xticklabels()} == {"insertion", "update", "deletion"}


def test_figures_build_without_error_on_full_synthetic_table():
    results = synthetic_results_table()
    figs = [
        plot_witness_cost_reads(results),
        plot_state_root_cost_writes(results),
        plot_leaf_stem_replay(results, "transaction"),
        plot_leaf_stem_replay(results, "block"),
        plot_basic_data_colocation(results),
        plot_mutation_kind(results),
    ]
    for fig in figs:
        assert isinstance(fig, Figure)
        assert any(ax.lines or ax.patches or ax.collections for ax in fig.axes)
