from __future__ import annotations

from matplotlib.figure import Figure

from apx.figures import (
    EMPHASIZED_S,
    TOUCHED_SERIES,
    WRITE_COACCESS_SERIES,
    WRITE_PURE_SERIES,
    plot_leaf_stem_replay,
    plot_state_root_cost_writes_coaccess,
    plot_state_root_cost_writes_pure,
    plot_witness_cost_touched,
)
from tests.fixtures import synthetic_results_table


def _data_lines(ax, min_points=3):
    """Real plotted lines, excluding zero-length legend-proxy artists."""
    return [line for line in ax.lines if len(line.get_xdata()) >= min_points]


def _vlines(ax):
    """axvline() artists: constant x, y spanning the full axes (0, 1)."""
    return [line for line in ax.lines if list(line.get_ydata()) == [0, 1]]


def test_plot_witness_cost_touched_has_one_pure_panel():
    results = synthetic_results_table()
    fig = plot_witness_cost_touched(results)
    assert isinstance(fig, Figure)
    assert len(fig.axes) == 1
    ax = fig.axes[0]

    assert len(_data_lines(ax)) == len(TOUCHED_SERIES)

    _, labels = ax.get_legend_handles_labels()
    assert set(labels) == set(TOUCHED_SERIES)

    # emphasized S values get an extra marker layer: one point per series per S
    assert max(len(c.get_offsets()) for c in ax.collections) == len(EMPHASIZED_S) * len(TOUCHED_SERIES)

    # current design (S=64) and metadata-only (S=0) should be marked as vertical lines
    assert sorted(line.get_xdata()[0] for line in _vlines(ax)) == [0, 64]


def test_plot_state_root_cost_writes_pure_and_coaccess_are_separate_figures():
    results = synthetic_results_table()
    pure_fig = plot_state_root_cost_writes_pure(results)
    coaccess_fig = plot_state_root_cost_writes_coaccess(results)
    assert isinstance(pure_fig, Figure)
    assert isinstance(coaccess_fig, Figure)
    assert len(pure_fig.axes) == 1
    assert len(coaccess_fig.axes) == 1
    pure_ax = pure_fig.axes[0]
    coaccess_ax = coaccess_fig.axes[0]

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


def test_figures_build_without_error_on_full_synthetic_table():
    results = synthetic_results_table()
    figs = [
        plot_witness_cost_touched(results),
        plot_state_root_cost_writes_pure(results),
        plot_state_root_cost_writes_coaccess(results),
        plot_leaf_stem_replay(results, "transaction"),
        plot_leaf_stem_replay(results, "block"),
    ]
    for fig in figs:
        assert isinstance(fig, Figure)
        assert any(ax.lines or ax.patches or ax.collections for ax in fig.axes)
