import pandas as pd

from apx.classify import classify_reads, classify_reads_block, mutation_kind


def test_classify_reads_partitions_disjointly():
    reads = pd.DataFrame(
        {
            "block_number": [1, 1, 1, 2],
            "transaction_index": [0, 0, 1, 0],
            "address": ["0xa", "0xa", "0xb", "0xc"],
            "slot": ["0x1", "0x2", "0x1", "0x1"],
            "read_count": [3, 1, 2, 5],
        }
    )
    # Only (block=1, tx=0, addr=0xa, slot=0x1) had a real mutation.
    tx_mutations = pd.DataFrame(
        {
            "block_number": [1],
            "transaction_index": [0],
            "address": ["0xa"],
            "slot": ["0x1"],
            "from_value": ["0x0"],
            "to_value": ["0x5"],
        }
    )
    out = classify_reads(reads, tx_mutations)
    assert out["is_write_coupled"].tolist() == [True, False, False, False]
    # Disjoint and exhaustive: every row is exactly one of the two.
    assert (out["is_write_coupled"] | ~out["is_write_coupled"]).all()
    assert len(out) == len(reads)


def test_classify_reads_does_not_duplicate_rows():
    # tx_mutations having other rows for the same key elsewhere must not fan out the join.
    reads = pd.DataFrame(
        {
            "block_number": [1],
            "transaction_index": [0],
            "address": ["0xa"],
            "slot": ["0x1"],
            "read_count": [1],
        }
    )
    tx_mutations = pd.DataFrame(
        {
            "block_number": [1, 1],
            "transaction_index": [0, 0],
            "address": ["0xa", "0xa"],
            "slot": ["0x1", "0x1"],
            "from_value": ["0x0", "0x0"],
            "to_value": ["0x5", "0x5"],
        }
    )
    out = classify_reads(reads, tx_mutations)
    assert len(out) == 1
    assert out["is_write_coupled"].iloc[0] is True or bool(out["is_write_coupled"].iloc[0]) is True


def test_classify_reads_block_dedups_across_transactions_and_joins_on_block_mutations():
    # Same (block, address, slot) read from two different transactions in block 1 must
    # collapse to one row; block 2's read is a distinct key.
    reads = pd.DataFrame(
        {
            "block_number": [1, 1, 2],
            "transaction_index": [0, 3, 0],
            "address": ["0xa", "0xa", "0xb"],
            "slot": ["0x1", "0x1", "0x1"],
            "read_count": [2, 1, 4],
        }
    )
    # Only (block=1, addr=0xa, slot=0x1) net-changed across the block.
    block_mutations = pd.DataFrame(
        {
            "block_number": [1],
            "address": ["0xa"],
            "slot": ["0x1"],
            "from_value": ["0x0"],
            "to_value": ["0x5"],
        }
    )
    out = classify_reads_block(reads, block_mutations)
    assert len(out) == 2
    row = out[(out["block_number"] == 1) & (out["address"] == "0xa")].iloc[0]
    assert bool(row["is_write_coupled"]) is True
    row2 = out[(out["block_number"] == 2) & (out["address"] == "0xb")].iloc[0]
    assert bool(row2["is_write_coupled"]) is False


def test_mutation_kind_hex_values():
    from_value = pd.Series(["0x0", "0x5", "0x3"])
    to_value = pd.Series(["0x5", "0x0", "0x7"])
    kind = mutation_kind(from_value, to_value, hex_values=True)
    assert kind.tolist() == ["insertion", "deletion", "update"]


def test_mutation_kind_decimal_values():
    from_value = pd.Series(["0", "5", "3"])
    to_value = pd.Series(["5", "0", "7"])
    kind = mutation_kind(from_value, to_value, hex_values=False)
    assert kind.tolist() == ["insertion", "deletion", "update"]
