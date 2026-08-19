from __future__ import annotations

from pathlib import Path

from apx.report import build_report
from tests.fixtures import synthetic_results_table, synthetic_validation


def test_build_report_writes_report_and_figures(tmp_path: Path):
    results = synthetic_results_table()
    validation = synthetic_validation()

    report_path = build_report(results, validation, tmp_path)

    assert report_path == tmp_path / "report.md"
    assert report_path.exists()

    fig_dir = tmp_path / "figures"
    expected_stems = [
        "witness_cost_reads",
        "state_root_cost_writes",
        "leaf_stem_transaction",
        "leaf_stem_block",
        "basic_data_colocation",
        "mutation_kind",
    ]
    for stem in expected_stems:
        path = fig_dir / f"{stem}.png"
        assert path.exists()
        assert path.stat().st_size > 0


def test_report_contains_required_sections():
    results = synthetic_results_table()
    validation = synthetic_validation()
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        report_path = build_report(results, validation, Path(tmp))
        text = report_path.read_text()

    required_headings = [
        "## Methodology summary",
        "## Data quality and reconciliation",
        "## Witness cost (reads)",
        "## State-root cost (writes)",
        "## Distinct leaf and stem replay",
        "## BASIC_DATA co-location",
        "## Mutation-kind diagnostics",
        "## Comparison against S=0 and current S=64",
        "## Limitations",
    ]
    for heading in required_headings:
        assert heading in text, f"missing section: {heading}"

    # figures embedded inline as images
    assert "![" in text and "figures/witness_cost_reads.png" in text
    assert "figures/state_root_cost_writes.png" in text
    assert "figures/leaf_stem_transaction.png" in text
    assert "figures/leaf_stem_block.png" in text
    assert "figures/basic_data_colocation.png" in text
    assert "figures/mutation_kind.png" in text


def test_report_renders_validation_dict_contents():
    results = synthetic_results_table()
    validation = {"custom_check": True, "rejected_rows": 42, "notes": ["a note", "another note"]}
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        report_path = build_report(results, validation, Path(tmp))
        text = report_path.read_text()

    assert "custom_check" in text
    assert "42" in text
    assert "a note" in text


def test_report_handles_empty_validation_dict():
    results = synthetic_results_table()
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        report_path = build_report(results, {}, Path(tmp))
        text = report_path.read_text()

    assert "## Data quality and reconciliation" in text


def test_report_has_no_dash_bulleted_lists():
    results = synthetic_results_table()
    validation = synthetic_validation()
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        report_path = build_report(results, validation, Path(tmp))
        text = report_path.read_text()

    for line in text.splitlines():
        stripped = line.strip()
        assert not stripped.startswith("- "), f"dash-bulleted line found: {line!r}"
