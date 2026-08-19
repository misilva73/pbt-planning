import pytest

from apx.config import load_config


def test_load_config_reads_credentials_from_env(tmp_path, monkeypatch):
    monkeypatch.setenv("CLICKHOUSE_USERNAME", "test-user")
    monkeypatch.setenv("CLICKHOUSE_PASSWORD", "test-pass")

    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "clickhouse:\n"
        "  host: example.invalid\n"
        "  port: 443\n"
        "  database: default\n"
        "  secure: true\n"
        "sampling:\n"
        "  end_block: 100\n"
        "  start_block: 1\n"
        "  bucket_size: 10\n"
    )

    config = load_config(config_path)

    assert config.clickhouse.host == "example.invalid"
    assert config.clickhouse.username == "test-user"
    assert config.clickhouse.password == "test-pass"
    assert config.sampling.start_block == 1


def test_load_config_raises_without_any_credentials(tmp_path, monkeypatch):
    monkeypatch.delenv("CLICKHOUSE_USERNAME", raising=False)
    monkeypatch.delenv("CLICKHOUSE_PASSWORD", raising=False)
    # Point REPO_ROOT-relative secrets.json lookup somewhere empty by monkeypatching the
    # module constant rather than touching the real repo-root secrets.json.
    import apx.config as config_module

    monkeypatch.setattr(config_module, "REPO_ROOT", tmp_path)

    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "clickhouse:\n"
        "  host: example.invalid\n"
        "  port: 443\n"
        "  database: default\n"
        "  secure: true\n"
        "sampling:\n"
        "  end_block: null\n"
        "  start_block: null\n"
        "  bucket_size: 10\n"
    )

    with pytest.raises(RuntimeError):
        load_config(config_path)
