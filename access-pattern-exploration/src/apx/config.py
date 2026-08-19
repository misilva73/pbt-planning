"""Configuration loading: non-secret settings from YAML, credentials from the environment."""

from __future__ import annotations

import json
import os
from pathlib import Path

import yaml
from pydantic import BaseModel

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = PROJECT_ROOT.parent


class ClickHouseConfig(BaseModel):
    host: str
    port: int
    database: str
    secure: bool
    username: str
    password: str


class SamplingConfig(BaseModel):
    end_block: int | None
    start_block: int | None
    bucket_size: int


class Config(BaseModel):
    clickhouse: ClickHouseConfig
    sampling: SamplingConfig


def _load_credentials() -> tuple[str, str]:
    """Read ClickHouse credentials from env vars, falling back to the repo-root secrets.json
    used in this workspace. A second researcher supplies their own via env vars."""
    username = os.environ.get("CLICKHOUSE_USERNAME")
    password = os.environ.get("CLICKHOUSE_PASSWORD")
    if username and password:
        return username, password

    secrets_path = REPO_ROOT / "secrets.json"
    if secrets_path.exists():
        secrets = json.loads(secrets_path.read_text())
        if "xatu_username" in secrets and "xatu_password" in secrets:
            return secrets["xatu_username"], secrets["xatu_password"]

    raise RuntimeError(
        "No ClickHouse credentials found. Set CLICKHOUSE_USERNAME / CLICKHOUSE_PASSWORD, "
        "or provide a secrets.json with xatu_username / xatu_password."
    )


def load_config(path: str | Path | None = None) -> Config:
    config_dir = PROJECT_ROOT / "config"
    if path is None:
        local = config_dir / "config.local.yaml"
        path = local if local.exists() else config_dir / "config.example.yaml"

    raw = yaml.safe_load(Path(path).read_text())
    username, password = _load_credentials()
    raw["clickhouse"]["username"] = username
    raw["clickhouse"]["password"] = password
    return Config.model_validate(raw)
