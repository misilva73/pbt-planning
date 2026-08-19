import pandas as pd

from apx.extraction import _stringify_big_ints, load_query, merge_chunks, QUERY_FILES


def test_load_query_formats_block_range():
    sql = load_query("storage_reads_agg", 100, 200)
    assert "BETWEEN 100 AND 200" in sql
    assert "canonical_execution_storage_reads" in sql


def test_load_query_covers_every_registered_query():
    for name in QUERY_FILES:
        sql = load_query(name, 1, 2)
        assert "BETWEEN 1 AND 2" in sql


def test_stringify_big_ints_converts_object_int_columns():
    df = pd.DataFrame({"value": [123, 2**200], "label": ["a", "b"]})
    out = _stringify_big_ints(df.copy())
    assert out["value"].tolist() == ["123", str(2**200)]
    assert out["label"].tolist() == ["a", "b"]


def test_stringify_big_ints_leaves_normal_columns_alone():
    df = pd.DataFrame({"n": pd.array([1, 2, 3], dtype="uint64"), "s": ["x", "y", "z"]})
    out = _stringify_big_ints(df.copy())
    pd.testing.assert_frame_equal(out, df)


def test_merge_chunks_concatenates_parts(tmp_path):
    chunk_dir = tmp_path / "chunks"
    out_dir = tmp_path / "merged"
    for name in QUERY_FILES:
        name_dir = chunk_dir / name
        name_dir.mkdir(parents=True)
        pd.DataFrame({"block_number": [1, 2]}).to_parquet(name_dir / "part-1-2.parquet")
        pd.DataFrame({"block_number": [3, 4]}).to_parquet(name_dir / "part-3-4.parquet")

    paths = merge_chunks(chunk_dir, out_dir)

    assert set(paths) == set(QUERY_FILES)
    for name, path in paths.items():
        df = pd.read_parquet(path)
        assert df["block_number"].tolist() == [1, 2, 3, 4]
