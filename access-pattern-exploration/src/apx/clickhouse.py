"""Thin ClickHouse client wrapper: every query returns a pandas DataFrame."""

from __future__ import annotations

import pandas as pd
import clickhouse_connect
from clickhouse_connect.driver.client import Client

from apx.config import ClickHouseConfig


def get_client(config: ClickHouseConfig) -> Client:
    return clickhouse_connect.get_client(
        host=config.host,
        port=config.port,
        username=config.username,
        password=config.password,
        database=config.database,
        secure=config.secure,
    )


def query_df(client: Client, sql: str, parameters: dict | None = None) -> pd.DataFrame:
    return client.query_df(sql, parameters=parameters)


def describe_table(client: Client, table: str) -> pd.DataFrame:
    return query_df(client, f"DESCRIBE TABLE {table}")
