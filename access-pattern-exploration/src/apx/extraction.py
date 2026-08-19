"""Run the pinned Part 1 queries against ClickHouse and cache results as parquet.

Every query is aggregated server-side (see queries/*.sql) so the client never downloads
raw event-level rows for the diff tables — only already-deduplicated mutation keys.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from apx.clickhouse import get_client, query_df
from apx.config import Config

QUERIES_DIR = Path(__file__).resolve().parents[2] / "queries"

QUERY_FILES = {
    "storage_reads_agg": "storage_reads_agg.sql",
    "storage_tx_mutations": "storage_tx_mutations.sql",
    "storage_block_mutations": "storage_block_mutations.sql",
    "balance_reads_agg": "balance_reads_agg.sql",
    "nonce_reads_agg": "nonce_reads_agg.sql",
    "balance_block_mutations": "balance_block_mutations.sql",
    "nonce_block_mutations": "nonce_block_mutations.sql",
}


def load_query(name: str, start_block: int, end_block: int) -> str:
    sql = (QUERIES_DIR / QUERY_FILES[name]).read_text()
    return sql.format(start_block=start_block, end_block=end_block)


def _stringify_big_ints(df: pd.DataFrame) -> pd.DataFrame:
    """ClickHouse UInt256 columns (e.g. balance from/to values) arrive as arbitrary-precision
    Python ints that overflow Arrow's int64 when writing parquet. Store them as decimal
    strings; callers that need the numeric value convert with int()."""
    for col in df.columns:
        if df[col].dtype == object and len(df) and isinstance(df[col].iloc[0], int):
            df[col] = df[col].astype(str)
    return df


def extract_one(config: Config, name: str, start_block: int, end_block: int) -> pd.DataFrame:
    client = get_client(config.clickhouse)
    sql = load_query(name, start_block, end_block)
    return query_df(client, sql)


def extract_all(
    config: Config,
    start_block: int,
    end_block: int,
    out_dir: Path,
    skip_existing: bool = True,
) -> dict[str, Path]:
    """Run every pinned query and cache each result as parquet under out_dir.

    Resumable: a query whose output parquet already exists is skipped unless
    skip_existing=False, so a partially-completed extraction can be re-run safely.

    Only suitable for ranges small enough to hold each query's full result in memory
    (a 10,000-block pilot already produces tens of millions of rows for the reads
    table). For the full 1,000,000-block Part 1 range, use extract_all_chunked instead.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    client = get_client(config.clickhouse)
    paths: dict[str, Path] = {}
    for name in QUERY_FILES:
        path = out_dir / f"{name}.parquet"
        paths[name] = path
        if skip_existing and path.exists():
            continue
        sql = load_query(name, start_block, end_block)
        df = _stringify_big_ints(query_df(client, sql))
        df.to_parquet(path, index=False)
    return paths


def extract_all_chunked(
    config: Config,
    start_block: int,
    end_block: int,
    out_dir: Path,
    chunk_size: int = 10_000,
) -> dict[str, Path]:
    """Run every pinned query over [start_block, end_block] in fixed-size block chunks,
    writing one parquet part per (query, chunk) under out_dir/<name>/part-<a>-<b>.parquet.

    Chunking by block range is safe here because every query GROUPs BY block_number
    (directly or via transaction_index within a block): rows from different chunks never
    need to be merged across chunks, only concatenated. Resumable at the chunk level — a
    part file that already exists is skipped, so a killed or interrupted run (this range
    is expected to take hours) can be restarted with the same call. Use merge_chunks() to
    collapse a chunk directory into the single-parquet-per-query layout extract_all
    produces, once done (or partially done, for interim inspection).
    """
    client = get_client(config.clickhouse)
    paths: dict[str, Path] = {}
    for name in QUERY_FILES:
        name_dir = out_dir / name
        name_dir.mkdir(parents=True, exist_ok=True)
        chunk_start = start_block
        while chunk_start <= end_block:
            chunk_end = min(chunk_start + chunk_size - 1, end_block)
            part_path = name_dir / f"part-{chunk_start}-{chunk_end}.parquet"
            if not part_path.exists():
                sql = load_query(name, chunk_start, chunk_end)
                df = _stringify_big_ints(query_df(client, sql))
                df.to_parquet(part_path, index=False)
            chunk_start = chunk_end + 1
        paths[name] = name_dir
    return paths


def merge_chunks(chunk_dir: Path, out_dir: Path) -> dict[str, Path]:
    """Concatenate each query's chunk parts (written by extract_all_chunked) into a single
    parquet file per query, matching the layout extract_all produces."""
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for name in QUERY_FILES:
        parts = sorted((chunk_dir / name).glob("part-*.parquet"))
        df = pd.concat((pd.read_parquet(p) for p in parts), ignore_index=True)
        path = out_dir / f"{name}.parquet"
        df.to_parquet(path, index=False)
        paths[name] = path
    return paths
