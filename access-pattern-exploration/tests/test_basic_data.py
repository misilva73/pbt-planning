import numpy as np
import pandas as pd

from apx.basic_data import (
    MUTATION_PROXY_KEYS,
    READ_PROXY_KEYS,
    build_mutation_proxy,
    build_read_proxy,
    colocation_curve,
)


def _slot_hex(v: int) -> str:
    return f"0x{v:064x}"


def test_build_read_proxy_unions_and_dedups():
    balance_reads = pd.DataFrame(
        {"block_number": [1, 1], "transaction_index": [0, 1], "address": ["0xa", "0xb"]}
    )
    nonce_reads = pd.DataFrame(
        {"block_number": [1, 1], "transaction_index": [0, 2], "address": ["0xa", "0xc"]}
    )
    proxy = build_read_proxy(balance_reads, nonce_reads)
    # (1,0,0xa) appears in both tables -> the union must not double-count it.
    assert len(proxy) == 3
    keys = set(proxy[READ_PROXY_KEYS].itertuples(index=False, name=None))
    assert keys == {(1, 0, "0xa"), (1, 1, "0xb"), (1, 2, "0xc")}


def test_build_mutation_proxy_unions_and_dedups():
    balance_muts = pd.DataFrame({"block_number": [1, 2], "address": ["0xa", "0xb"]})
    nonce_muts = pd.DataFrame({"block_number": [1, 3], "address": ["0xa", "0xc"]})
    proxy = build_mutation_proxy(balance_muts, nonce_muts)
    assert len(proxy) == 3
    keys = set(proxy[MUTATION_PROXY_KEYS].itertuples(index=False, name=None))
    assert keys == {(1, "0xa"), (2, "0xb"), (3, "0xc")}


def test_colocation_curve_hand_computed():
    # Two low-index (slot < some S) storage reads for addr 0xa in (block=1, tx=0): one
    # matches the read proxy (0xa was also balance/nonce-read there), one for addr 0xb
    # does not. A third, higher-slot event for 0xa must not count as "low-index" at all.
    storage = pd.DataFrame(
        {
            "block_number": [1, 1, 1],
            "transaction_index": [0, 0, 0],
            "address": ["0xa", "0xb", "0xa"],
            "slot": [_slot_hex(1), _slot_hex(2), _slot_hex(200)],
        }
    )
    proxy = pd.DataFrame({"block_number": [1], "transaction_index": [0], "address": ["0xa"]})
    weight = np.array([1.0, 1.0, 1.0])
    matched, total = colocation_curve(storage, proxy, READ_PROXY_KEYS, weight, s_values=[0, 3, 200])

    assert total[0] == 0.0  # no event has slot < 0
    assert matched[0] == 0.0
    assert total[3] == 2.0  # slots 1 and 2 are < 3; slot 200 is not
    assert matched[3] == 1.0  # only the 0xa row (slot 1) matches the proxy
    assert total[200] == 2.0  # slot 200 is still not < 200
    assert matched[200] == 1.0
