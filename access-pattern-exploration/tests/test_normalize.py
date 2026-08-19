import pandas as pd

from apx.normalize import (
    normalize_address_column,
    normalize_addresses,
    normalize_addresses_and_slots,
    normalize_slot_column,
)


def test_normalize_address_column_accepts_valid_and_lowercases():
    series = pd.Series(["0x" + "AB" * 20, "0x" + "cd" * 20])
    cleaned, n_rejected = normalize_address_column(series)
    assert n_rejected == 0
    assert cleaned.tolist() == ["0x" + "ab" * 20, "0x" + "cd" * 20]


def test_normalize_address_column_rejects_malformed_and_reports_count():
    series = pd.Series(
        [
            "0x" + "ab" * 20,  # valid
            "0x" + "ab" * 19,  # too short
            "not_hex_at_all",  # not hex
            "0x" + "gg" * 20,  # non-hex characters
            None,  # missing
        ]
    )
    cleaned, n_rejected = normalize_address_column(series)
    assert n_rejected == 4
    assert cleaned.tolist() == ["0x" + "ab" * 20]


def test_normalize_slot_column_rejects_wrong_width():
    series = pd.Series(["0x" + "1" * 64, "0x" + "1" * 63, "0x" + "1" * 65])
    cleaned, n_rejected = normalize_slot_column(series)
    assert n_rejected == 2
    assert cleaned.tolist() == ["0x" + "1" * 64]


def test_normalize_addresses_drops_rejects_and_keeps_other_columns():
    df = pd.DataFrame(
        {
            "address": ["0x" + "ab" * 20, "bad"],
            "read_count": [3, 7],
        }
    )
    out, n_rejected = normalize_addresses(df)
    assert n_rejected == 1
    assert out["read_count"].tolist() == [3]


def test_normalize_addresses_and_slots_reports_independently():
    df = pd.DataFrame(
        {
            "address": ["0x" + "ab" * 20, "bad_address", "0x" + "cd" * 20],
            "slot": ["0x" + "1" * 64, "0x" + "2" * 64, "not_a_slot"],
        }
    )
    out, rejects = normalize_addresses_and_slots(df)
    # Row 0: both valid -> kept. Row 1: bad address -> dropped. Row 2: bad slot -> dropped.
    assert len(out) == 1
    assert out["address"].tolist() == ["0x" + "ab" * 20]
    assert rejects == {"address_rejected": 1, "slot_rejected": 1}
